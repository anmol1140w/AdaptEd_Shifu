"""Qdrant Cloud adapter for NCERT retrieval, implementing the app retrieval port."""
from __future__ import annotations

import re

from backend.app.application.ports.ai import (
    RetrievalPort,
    RetrievalRequest,
    RetrievalResult,
    RetrievedSource,
)
from backend.app.infrastructure.ai.settings import AISettings
from qdrant_client import QdrantClient, models

ACTIVE_ALIAS = "ncert_pcm_active"
MODEL = "sentence-transformers/all-minilm-l6-v2"


def _read_client() -> QdrantClient:
    settings = AISettings()
    url = settings.qdrant_url.strip()
    api_key = settings.qdrant_read_only_api_key.strip()
    if not url or not api_key:
        raise RuntimeError(
            "Set QDRANT_URL and QDRANT_READ_ONLY_API_KEY in backend/.env "
            "or the process environment"
        )
    return QdrantClient(url=url, api_key=api_key, cloud_inference=True, timeout=30)


_SUBJECT_ALIASES = {
    "physics": "Physics",
    "phy": "Physics",
    "chemistry": "Chemistry",
    "chem": "Chemistry",
    "mathematics": "Mathematics",
    "math": "Mathematics",
}


class QdrantNcertRetriever(RetrievalPort):
    """Semantic retrieval constrained to the requested subject, class, and concept."""

    def __init__(self, *, client=None, collection: str = ACTIVE_ALIAS, top_k: int = 5) -> None:
        if top_k < 1 or top_k > 20:
            raise ValueError("top_k must be between 1 and 20")
        self._client = client or _read_client()
        self._collection = collection
        self._top_k = top_k

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        subject_key = request.subject_id.strip().lower().replace("_", " ")
        subject = _SUBJECT_ALIASES.get(subject_key)
        if subject is None:
            # Some clients use IDs such as "subject-physics".
            subject = next((name for key, name in _SUBJECT_ALIASES.items() if key in subject_key), None)
        if subject is None:
            return RetrievalResult()

        grade_match = re.search(r"(?:^|[-_])((?:11|12))(?:[-_]|$)", request.concept_id)
        if not grade_match:
            return RetrievalResult()
        grade = int(grade_match.group(1))
        filters = [
            models.FieldCondition(key="subject", match=models.MatchValue(value=subject)),
            models.FieldCondition(key="class", match=models.MatchValue(value=grade)),
            models.FieldCondition(key="concept_ids", match=models.MatchValue(value=request.concept_id)),
        ]
        query_parts = [request.query.strip(), f"Subject: {subject}", f"Class: {grade}", f"Concept: {request.concept_id}"]
        if request.misconception:
            query_parts.append(f"Likely misconception: {request.misconception.strip()}")
        response = self._client.query_points(
            collection_name=self._collection,
            query=models.Document(text="\n".join(query_parts), model=MODEL),
            query_filter=models.Filter(must=filters),
            limit=self._top_k,
            with_payload=True,
            timeout=30,
        )
        sources: list[RetrievedSource] = []
        for point in response.points:
            payload = point.payload or {}
            text = str(payload.get("page_content", "")).strip()
            if not text:
                continue
            score = max(0.0, min(1.0, float(point.score or 0.0)))
            parent_id = str(payload.get("parent_chunk_id", payload.get("chunk_id", point.id)))
            segment = int(payload.get("embedding_segment", 0))
            source_id = f"{parent_id}:segment:{segment}"
            citation = str(payload.get("citation", "NCERT textbook source"))
            sources.append(RetrievedSource(
                source_id=source_id,
                subject_id=request.subject_id,
                concept_id=request.concept_id,
                title=citation,
                text=text,
                confidence=score,
                approved=True,
            ))
        confidence = max((source.confidence for source in sources), default=0.0)
        return RetrievalResult(sources=tuple(sources), confidence=confidence)
