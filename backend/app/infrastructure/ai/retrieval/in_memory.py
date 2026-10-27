"""Dependency-free retrieval adapter over approved source chunks."""

from __future__ import annotations

from collections.abc import Iterable

from ....application.ports.ai import (
    RetrievedSource,
    RetrievalPort,
    RetrievalRequest,
    RetrievalResult,
)


class InMemoryLearningRetriever(RetrievalPort):
    """Return stable approved sources matching subject and concept IDs."""

    def __init__(self, sources: Iterable[RetrievedSource]) -> None:
        source_list = tuple(sources)
        source_ids = [source.source_id for source in source_list]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("learning source IDs must be unique")
        self._sources = source_list

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        matching = tuple(
            sorted(
                (
                    source
                    for source in self._sources
                    if source.approved
                    and source.subject_id == request.subject_id
                    and source.concept_id == request.concept_id
                ),
                key=lambda source: (-source.confidence, source.source_id),
            )
        )
        confidence = max((source.confidence for source in matching), default=0.0)
        return RetrievalResult(sources=matching, confidence=confidence)
