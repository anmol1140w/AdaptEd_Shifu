"""Validated, repeatable NCERT-to-Qdrant Cloud ingestion pipeline.

Usage from the repository root:
    python -m content.datasets.ncert.qdrant_pipeline validate
    python -m content.datasets.ncert.qdrant_pipeline ingest --strategy heading_aware_650_words
    python -m content.datasets.ncert.qdrant_pipeline search "Explain conservation of momentum" --subject Physics --grade 11

Qdrant Cloud credentials are read only from QDRANT_URL and QDRANT_API_KEY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

from qdrant_client import QdrantClient, models
from backend.app.infrastructure.ai.settings import AISettings

ROOT = Path(__file__).resolve().parents[3]
CORPUS_ROOT = ROOT / "content/datasets/ncert/chunks"
BOOKS_ROOT = ROOT / "content/books"
STRATEGIES = ("page", "heading_aware_650_words", "fixed_450_words_overlap_75")
MODEL = "sentence-transformers/all-minilm-l6-v2"
VECTOR_SIZE = 384
PIPELINE_SCHEMA_VERSION = "2"
SEGMENT_MAX_WORDS = 64
SEGMENT_OVERLAP_WORDS = 10
ACTIVE_ALIAS = "ncert_pcm_active"
NAMESPACE = uuid.UUID("19aecab7-c359-4c48-8523-6db9eff38488")
LOG = logging.getLogger("ncert_qdrant")


# The source corpora preserve chapter codes and titles; these title variants
# reconcile the authored concept catalog with the corresponding official NCERT
# chapter title without changing any stable concept IDs.
TITLE_ALIASES = {
    "classification of elements and periodicity": "classification of elements and periodicity in properties",
    "organic chemistry some basic principles": "organic chemistry some basic principles and techniques",
    "vectors": "vector algebra",
    "three dimensional geometry": "three dimensional geometry",
    "application of integrals": "applications of integrals",
    "ray optics": "ray optics and optical instruments",
    "the d and f block elements": "d and f block elements",
}


def _norm_title(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return TITLE_ALIASES.get(key, key)


def _concept_lookup() -> dict[tuple[int, str, str], tuple[str, ...]]:
    """Build chapter -> concept links from the authored class book manifests."""
    index: dict[tuple[int, str, str], set[str]] = defaultdict(set)
    for path in BOOKS_ROOT.glob("*_class_*.json"):
        try:
            book = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Cannot read concept mapping source {path}: {exc}") from exc
        grade = int(book["class"])
        subject = str(book["subject"]).strip().lower()
        for chapter in book.get("chapters", []):
            title = _norm_title(str(chapter.get("chapter_title", "")))
            concept_id = str(chapter.get("concept_id", "")).strip()
            if title and concept_id:
                index[(grade, subject, title)].add(concept_id)
    return {key: tuple(sorted(values)) for key, values in index.items()}


def _read_records(strategy: str) -> Iterator[tuple[Path, int, dict[str, Any]]]:
    folder = CORPUS_ROOT / strategy
    if not folder.is_dir():
        raise FileNotFoundError(f"No corpus for strategy {strategy!r}: {folder}")
    paths = sorted(folder.rglob("*.jsonl"))
    if not paths:
        raise FileNotFoundError(f"No JSONL chapter files under {folder}")
    for path in paths:
        with path.open(encoding="utf-8") as source:
            for line_no, line in enumerate(source, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {path}:{line_no}: {exc}") from exc
                yield path, line_no, record


def _validate_record(path: Path, line_no: int, record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict) or not isinstance(record.get("metadata"), dict):
        raise ValueError(f"Expected page_content and metadata object at {path}:{line_no}")
    text = record.get("page_content")
    meta = record["metadata"]
    required = ("chunk_id", "source_id", "class", "subject", "chapter_code", "chapter_title",
                "page_start", "page_end", "source_pdf_path", "citation", "chunking_strategy")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Empty page_content at {path}:{line_no}")
    missing = [key for key in required if key not in meta or meta[key] in (None, "")]
    if missing:
        raise ValueError(f"Missing metadata {missing} at {path}:{line_no}")
    if int(meta["page_start"]) < 1 or int(meta["page_end"]) < int(meta["page_start"]):
        raise ValueError(f"Invalid citation page span at {path}:{line_no}")
    source_pdf = ROOT / str(meta["source_pdf_path"])
    if not source_pdf.is_file():
        raise FileNotFoundError(f"Citation source PDF missing at {path}:{line_no}: {source_pdf}")
    for key, value in meta.items():
        if not isinstance(value, (str, int, float, bool)) and value is not None:
            raise ValueError(f"Metadata {key!r} is not a scalar at {path}:{line_no}")
    return meta


def _split_embedding_text(
    text: str,
    max_words: int = SEGMENT_MAX_WORDS,
    overlap_words: int = SEGMENT_OVERLAP_WORDS,
) -> list[str]:
    """Conservatively bound model input while preserving original text in source files."""
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]
    parts: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        parts.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_words
    return parts


def _stable_point_id(strategy: str, chunk_id: str, segment: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{strategy}:{chunk_id}:{segment}"))


def _concepts_for(meta: dict[str, Any], mapping: dict[tuple[int, str, str], tuple[str, ...]]) -> tuple[str, ...]:
    return mapping.get((int(meta["class"]), str(meta["subject"]).lower(), _norm_title(str(meta["chapter_title"]))), ())


def validate_corpus(strategy: str) -> tuple[int, int, int, dict[tuple[int, str, str], tuple[str, ...]]]:
    mapping = _concept_lookup()
    records = indexed_records = segments = 0
    unmatched: set[str] = set()
    for path, line_no, record in _read_records(strategy):
        meta = _validate_record(path, line_no, record)
        records += 1
        concepts = _concepts_for(meta, mapping)
        if not concepts:
            unmatched.add(f"{meta['class']} {meta['subject']} {meta['chapter_code']} {meta['chapter_title']}")
            continue
        indexed_records += 1
        segments += len(_split_embedding_text(record["page_content"]))
    if unmatched:
        LOG.warning("%d source chapters have no authored concept mapping", len(unmatched))
        for item in sorted(unmatched):
            LOG.warning("Unmapped chapter: %s", item)
    return records, indexed_records, segments, mapping


def _corpus_fingerprint(strategy: str) -> str:
    digest = hashlib.sha256()
    digest.update(f"{PIPELINE_SCHEMA_VERSION}:{MODEL}:{VECTOR_SIZE}:{SEGMENT_MAX_WORDS}:{SEGMENT_OVERLAP_WORDS}".encode())
    for path in sorted((CORPUS_ROOT / strategy).rglob("*.jsonl")):
        digest.update(path.relative_to(CORPUS_ROOT / strategy).as_posix().encode())
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(block)
    # Mapping changes are corpus changes too.
    for path in sorted(BOOKS_ROOT.glob("*_class_*.json")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def _qdrant_client(*, read_only: bool = False) -> QdrantClient:
    settings = AISettings()
    url = settings.qdrant_url.strip()
    api_key = (
        settings.qdrant_read_only_api_key.strip() or settings.qdrant_api_key.strip()
        if read_only else settings.qdrant_api_key.strip()
    )
    if not url or not api_key:
        required = "QDRANT_URL and QDRANT_READ_ONLY_API_KEY" if read_only else "QDRANT_URL and QDRANT_API_KEY"
        raise RuntimeError(f"Set {required} in the backend environment")
    return QdrantClient(url=url, api_key=api_key, cloud_inference=True, timeout=60)


def _make_collection(client: QdrantClient, name: str) -> None:
    schemas = {
        "subject": models.PayloadSchemaType.KEYWORD,
        "class": models.PayloadSchemaType.INTEGER,
        "book_part": models.PayloadSchemaType.KEYWORD,
        "chapter_code": models.PayloadSchemaType.KEYWORD,
        "concept_ids": models.PayloadSchemaType.KEYWORD,
        "chunking_strategy": models.PayloadSchemaType.KEYWORD,
        "page_start": models.PayloadSchemaType.INTEGER,
        "page_end": models.PayloadSchemaType.INTEGER,
    }
    if client.collection_exists(name):
        info = client.get_collection(name)
        vectors = info.config.params.vectors
        if not isinstance(vectors, models.VectorParams):
            raise RuntimeError(f"Existing collection {name} has an incompatible named-vector layout")
        if vectors.size != VECTOR_SIZE or vectors.distance != models.Distance.COSINE:
            raise RuntimeError(f"Existing collection {name} has incompatible vector config")
        existing_indexes = info.payload_schema or {}
        for field, schema in schemas.items():
            if field not in existing_indexes:
                client.create_payload_index(collection_name=name, field_name=field, field_schema=schema, wait=True)
        return
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
    )
    for field, schema in schemas.items():
        client.create_payload_index(collection_name=name, field_name=field, field_schema=schema, wait=True)


def _atomic_activate(client: QdrantClient, collection: str) -> None:
    aliases = client.get_aliases().aliases
    existing = next((a for a in aliases if a.alias_name == ACTIVE_ALIAS), None)
    if existing and existing.collection_name == collection:
        return
    actions: list[Any] = []
    if existing:
        actions.append(models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=ACTIVE_ALIAS)))
    actions.append(models.CreateAliasOperation(create_alias=models.CreateAlias(
        collection_name=collection, alias_name=ACTIVE_ALIAS)))
    client.update_collection_aliases(change_aliases_operations=actions, timeout=60)


def ingest(strategy: str, batch_size: int = 64, activate: bool = True) -> str:
    records, indexed_records, expected_points, concept_map = validate_corpus(strategy)
    fingerprint = _corpus_fingerprint(strategy)
    safe_strategy = strategy.replace("_", "")
    collection = f"ncertpcm_{safe_strategy}_minilm_{fingerprint}"
    LOG.info("Preparing %d mapped source chunks from %d total chunks as %d embedding points",
             indexed_records, records, expected_points)
    client = _qdrant_client()
    _make_collection(client, collection)

    batch: list[models.PointStruct] = []
    sent = 0
    for path, line_no, record in _read_records(strategy):
        meta = _validate_record(path, line_no, record)
        normalized = dict(meta)
        normalized["content_flags"] = [x for x in str(meta.get("content_flags", "")).split(",") if x]
        concepts = _concepts_for(meta, concept_map)
        # Do not expose answer keys, preliminaries, appendices, or source chapters
        # with no AdaptEd concept mapping to student-facing retrieval.
        if not concepts:
            continue
        normalized["concept_ids"] = list(concepts)
        normalized["mapping_basis"] = "authored_book_chapter_title"
        normalized["source_status"] = "official_ncert_text_extraction"
        normalized["text_is_extracted_not_visual_transcription"] = True
        segments = _split_embedding_text(record["page_content"])
        for number, segment in enumerate(segments):
            payload = {
                "page_content": segment,
                "parent_chunk_id": str(meta["chunk_id"]),
                "embedding_segment": number,
                "embedding_segment_count": len(segments),
                **normalized,
            }
            batch.append(models.PointStruct(
                id=_stable_point_id(strategy, str(meta["chunk_id"]), number),
                vector=models.Document(text=segment, model=MODEL),
                payload=payload,
            ))
            if len(batch) >= batch_size:
                _upsert_with_retry(client, collection, batch)
                sent += len(batch)
                LOG.info("Indexed %d/%d points", sent, expected_points)
                batch.clear()
    if batch:
        _upsert_with_retry(client, collection, batch)
        sent += len(batch)
    count = client.count(collection_name=collection, exact=True).count
    if count != expected_points:
        raise RuntimeError(f"Ingestion incomplete: expected {expected_points} points, collection has {count}")
    if activate:
        _atomic_activate(client, collection)
    LOG.info("Ingested %d points into %s%s", count, collection, f" and activated {ACTIVE_ALIAS}" if activate else "")
    return collection


def _upsert_with_retry(client: QdrantClient, collection: str, points: list[models.PointStruct]) -> None:
    for attempt in range(1, 6):
        try:
            client.upsert(collection_name=collection, points=points, wait=True, timeout=120)
            return
        except Exception:
            if attempt == 5:
                raise
            delay = min(2 ** (attempt - 1), 16)
            LOG.exception("Qdrant upsert failed (attempt %d/5); retrying in %ds", attempt, delay)
            time.sleep(delay)


def search(query: str, subject: str, grade: int, concept_id: str | None, limit: int = 5) -> list[Any]:
    client = _qdrant_client()
    filters: list[Any] = [
        models.FieldCondition(key="subject", match=models.MatchValue(value=subject)),
        models.FieldCondition(key="class", match=models.MatchValue(value=grade)),
    ]
    if concept_id:
        filters.append(models.FieldCondition(key="concept_ids", match=models.MatchValue(value=concept_id)))
    result = client.query_points(
        collection_name=ACTIVE_ALIAS,
        query=models.Document(text=query, model=MODEL),
        query_filter=models.Filter(must=filters),
        limit=limit,
        with_payload=True,
        timeout=60,
    )
    return result.points


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate", help="validate source rows, citations, and mappings without cloud access")
    validate_parser.add_argument("--strategy", choices=STRATEGIES, default="heading_aware_650_words")
    ingest_parser = sub.add_parser("ingest", help="build a versioned Qdrant collection and atomically activate it")
    ingest_parser.add_argument("--strategy", choices=STRATEGIES, required=True)
    ingest_parser.add_argument("--batch-size", type=int, default=64)
    ingest_parser.add_argument("--no-activate", action="store_true")
    query_parser = sub.add_parser("search", help="query the active collection for a retrieval smoke check")
    query_parser.add_argument("query")
    query_parser.add_argument("--subject", required=True, choices=("Physics", "Chemistry", "Mathematics"))
    query_parser.add_argument("--grade", type=int, required=True, choices=(11, 12))
    query_parser.add_argument("--concept-id")
    query_parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    try:
        if args.command == "validate":
            rows, indexed_rows, points, mapping = validate_corpus(args.strategy)
            print(json.dumps({"strategy": args.strategy, "source_chunks": rows,
                              "indexed_concept_mapped_chunks": indexed_rows, "embedding_points": points,
                              "mapped_chapter_concepts": len(mapping)}, indent=2))
        elif args.command == "ingest":
            if args.batch_size < 1 or args.batch_size > 256:
                raise ValueError("batch-size must be between 1 and 256")
            print(ingest(args.strategy, args.batch_size, not args.no_activate))
        else:
            points = search(args.query, args.subject, args.grade, args.concept_id, args.limit)
            for point in points:
                payload = point.payload or {}
                print(json.dumps({"score": point.score, "text": payload.get("page_content"),
                                  "citation": payload.get("citation"), "source_pdf_path": payload.get("source_pdf_path"),
                                  "chunk_id": payload.get("parent_chunk_id"), "concept_ids": payload.get("concept_ids", [])}, ensure_ascii=False))
        return 0
    except Exception as exc:
        LOG.exception("Qdrant corpus pipeline failed")
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
