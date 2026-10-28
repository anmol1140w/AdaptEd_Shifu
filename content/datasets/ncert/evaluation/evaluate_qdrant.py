"""Evaluate both production-like and oracle-concept Qdrant retrieval modes."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from qdrant_client import QdrantClient, models
from backend.app.infrastructure.ai.settings import AISettings
from content.datasets.ncert.qdrant_pipeline import ACTIVE_ALIAS, CORPUS_ID, MODEL, SOURCE_KIND, _concept_lookup, _norm_title

ROOT = Path(__file__).resolve().parents[4]
EVAL = Path(__file__).with_name("questions.jsonl")
CATALOG = json.loads((ROOT / "content/books/ncert/catalog.json").read_text(encoding="utf-8"))
CHAPTERS = {(b["class"], b["subject"].lower(), ch["chapter_code"]): ch["chapter_title"] for b in CATALOG["books"] for ch in b["chapters"]}
SUBJECTS = {"physics": "Physics", "chemistry": "Chemistry", "mathematics": "Mathematics"}


def _dedupe(points) -> list[dict]:
    unique: list[dict] = []
    seen: set[str] = set()
    for point in sorted(points, key=lambda p: float(p.score or 0), reverse=True):
        payload = point.payload or {}
        key = str(payload.get("parent_chunk_id", payload.get("chunk_id", point.id)))
        if key in seen:
            continue
        seen.add(key)
        unique.append({
            "chapter_code": payload.get("chapter_code"),
            "chunk_id": payload.get("parent_chunk_id", payload.get("chunk_id")),
            "citation": payload.get("citation"),
            "page_start": payload.get("page_start"),
            "page_end": payload.get("page_end"),
            "score": float(point.score or 0),
            "source_kind": payload.get("source_kind"),
            "corpus_id": payload.get("corpus_id"),
        })
    return unique[:8]


def _search(client, target: str, query: str, subject: str, class_level: int, model: str, concept_id: str | None = None):
    must = [
        models.FieldCondition(key="corpus_id", match=models.MatchValue(value=CORPUS_ID)),
        models.FieldCondition(key="source_kind", match=models.MatchValue(value=SOURCE_KIND)),
        models.FieldCondition(key="subject", match=models.MatchValue(value=subject)),
        models.FieldCondition(key="class", match=models.MatchValue(value=class_level)),
    ]
    if concept_id:
        must.append(models.FieldCondition(key="concept_ids", match=models.MatchValue(value=concept_id)))
    result = client.query_points(
        collection_name=target,
        query=models.Document(text=query, model=model),
        query_filter=models.Filter(must=must),
        limit=8 if concept_id is None else 5,
        with_payload=True,
        timeout=45,
    )
    return result.points


def _chapter_metrics(rows: list[dict], hit_key: str) -> dict:
    answerable = [row for row in rows if row["answerable"] and row["expected_chapter_codes"]]
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    precisions: list[float] = []
    citation_valid: list[float] = []
    for row in answerable:
        hits = row[hit_key][:5]
        expected = set(row["expected_chapter_codes"])
        found = [str(hit.get("chapter_code")) for hit in hits]
        ranks = [index for index, code in enumerate(found, 1) if code in expected]
        recalls.append(len(set(found) & expected) / len(expected))
        reciprocal_ranks.append(1 / ranks[0] if ranks else 0.0)
        precisions.append(sum(code in expected for code in found) / max(len(found), 1))
        citation_valid.append(sum(
            bool(hit.get("chunk_id") and hit.get("citation") and hit.get("page_start") and hit.get("page_end") and hit.get("source_kind") == SOURCE_KIND and hit.get("corpus_id") == CORPUS_ID)
            for hit in hits
        ) / max(len(hits), 1))
    return {
        "answerable_queries": len(answerable),
        "chapter_recall_at_5": round(sum(recalls) / max(len(recalls), 1), 4),
        "mrr_at_5": round(sum(reciprocal_ranks) / max(len(reciprocal_ranks), 1), 4),
        "chapter_citation_precision_at_5": round(sum(precisions) / max(len(precisions), 1), 4),
        "citation_payload_integrity_at_5": round(sum(citation_valid) / max(len(citation_valid), 1), 4),
    }


def _by_class_subject(rows: list[dict], hit_key: str) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[f"class_{row['class']}_{row['subject'].lower()}"].append(row)
    return {key: _chapter_metrics(value, hit_key) for key, value in sorted(grouped.items())}


def _threshold_sweep(rows: list[dict]) -> list[dict]:
    """Show the precision/abstention trade-off before changing runtime cutoffs."""
    answerable = [row for row in rows if row["answerable"]]
    unanswerable = [row for row in rows if not row["answerable"]]
    results = []
    for threshold in (0.50, 0.55, 0.60, 0.61, 0.62, 0.65, 0.70):
        filtered = [
            {**row, "subject_class_hits": [hit for hit in row["subject_class_hits"] if hit["score"] >= threshold]}
            for row in rows
        ]
        metrics = _chapter_metrics(filtered, "subject_class_hits")
        results.append({
            "threshold": threshold,
            **metrics,
            "answerable_queries_without_hit": sum(not any(hit["score"] >= threshold for hit in row["subject_class_hits"]) for row in answerable),
            "unanswerable_queries_with_hit": sum(bool(row["subject_class_hits"]) and row["subject_class_hits"][0]["score"] >= threshold for row in unanswerable),
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", help="evaluate a candidate collection without activating it")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("qdrant_results.json"), help="write detailed results to this JSON file")
    args = parser.parse_args()
    settings = AISettings()
    if not settings.qdrant_url or not settings.qdrant_read_only_api_key:
        raise SystemExit("Qdrant read-only configuration missing")
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_read_only_api_key, cloud_inference=True, timeout=45)
    aliases = {alias.alias_name: alias.collection_name for alias in client.get_aliases().aliases}
    if ACTIVE_ALIAS not in aliases:
        raise SystemExit(f"{ACTIVE_ALIAS} alias is not configured")
    target = args.collection or ACTIVE_ALIAS
    if args.collection and not client.collection_exists(target):
        raise SystemExit(f"candidate collection does not exist: {target}")
    concepts = _concept_lookup()
    queries = [json.loads(line) for line in EVAL.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = []
    for query in queries:
        expected = query["expected_chapter_codes"]
        expected_concepts = []
        for code in expected:
            title = CHAPTERS.get((query["class"], query["subject"].lower(), code))
            if title:
                expected_concepts.extend(concepts.get((query["class"], query["subject"].lower(), _norm_title(title)), ()))
        subject = SUBJECTS[query["subject"].lower()]
        broad = _dedupe(_search(client, target, query["query"], subject, query["class"], MODEL))
        oracle_points = []
        for concept_id in dict.fromkeys(expected_concepts):
            oracle_points.extend(_search(client, target, query["query"], subject, query["class"], MODEL, concept_id))
        oracle = _dedupe(oracle_points)
        rows.append({
            "id": query["id"], "class": query["class"], "subject": query["subject"],
            "category": query.get("category"), "answerable": query["answerable"],
            "expected_chapter_codes": expected, "oracle_concepts": list(dict.fromkeys(expected_concepts)),
            "subject_class_hits": broad, "oracle_concept_hits": oracle,
        })

    negative = [row for row in rows if not row["answerable"]]
    summary = {
        "evaluated_target": target,
        "target_is_active": target == ACTIVE_ALIAS or aliases[ACTIVE_ALIAS] == target,
        "model": MODEL,
        "questions": len(rows),
        "answerable": sum(row["answerable"] for row in rows),
        "unanswerable": len(negative),
        "subject_class_retrieval": _chapter_metrics(rows, "subject_class_hits"),
        "oracle_concept_retrieval": _chapter_metrics(rows, "oracle_concept_hits"),
        "by_class_subject": _by_class_subject(rows, "subject_class_hits"),
        "unanswerable_subject_class": {
            "with_any_hit": sum(bool(row["subject_class_hits"]) for row in negative),
            "top_score_ge_0_6": sum(bool(row["subject_class_hits"]) and row["subject_class_hits"][0]["score"] >= 0.6 for row in negative),
        },
        "threshold_0_6_subject_class": _chapter_metrics([
            {**row, "subject_class_hits": [hit for hit in row["subject_class_hits"] if hit["score"] >= 0.6]}
            for row in rows
        ], "subject_class_hits"),
        "subject_class_threshold_sweep": _threshold_sweep(rows),
        "note": "Subject/class retrieval approximates cross-concept production search. Oracle-concept metrics use expected labels and are an upper bound, not the production query. Citation payload integrity checks identifier and provenance fields; chapter-level labels do not prove passage-level answer support.",
    }
    out = args.output
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "queries": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Details written to {out}")


if __name__ == "__main__":
    main()
