"""Aggregate explainable concept evidence into a learner subject summary."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from ...domain.entities.learning import (
    AttemptEvidence,
    Concept,
    GapStatus,
    MasteryState,
    Recommendation,
)
from ...domain.services.learning_engine import LearningEngine
from ..ports.assessment import ConceptCatalogPort
from ..ports.learning import AttemptPort, MasteryStatePort


@dataclass(frozen=True, slots=True)
class BuildSubjectSummaryCommand:
    """Input required to build one learner's subject summary."""

    learner_id: str
    subject_id: str

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner id must not be empty")
        if not self.subject_id.strip():
            raise ValueError("subject id must not be empty")


@dataclass(frozen=True, slots=True)
class ConceptSummary:
    """A concept-level drill-down within a subject summary."""

    concept: Concept
    mastery_state: MasteryState | None
    gap_status: GapStatus
    recommendation: Recommendation | None
    evidence: tuple[AttemptEvidence, ...] = ()

    def __post_init__(self) -> None:
        evidence = tuple(self.evidence)
        if any(attempt.concept_id != self.concept.id for attempt in evidence):
            raise ValueError("concept summary evidence does not match its concept")
        if self.mastery_state is not None and self.mastery_state.concept_id != self.concept.id:
            raise ValueError("concept summary mastery does not match its concept")
        if not isinstance(self.gap_status, GapStatus):
            object.__setattr__(self, "gap_status", GapStatus(self.gap_status))
        object.__setattr__(self, "evidence", evidence)


@dataclass(frozen=True, slots=True)
class SubjectSummary:
    """Aggregated subject metrics with traceable concept-level evidence."""

    learner_id: str
    subject_id: str
    concepts: tuple[ConceptSummary, ...]
    mastery_score: float
    confidence: float
    evidence_count: int
    gap_status_counts: tuple[tuple[GapStatus, int], ...]

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("summary learner id must not be empty")
        if not self.subject_id.strip():
            raise ValueError("summary subject id must not be empty")
        concepts = tuple(self.concepts)
        if not concepts:
            raise ValueError("subject summary must contain at least one concept")
        concept_ids = [summary.concept.id for summary in concepts]
        if len(concept_ids) != len(set(concept_ids)):
            raise ValueError("subject summary concept IDs must be unique")
        if any(summary.concept.subject_id != self.subject_id for summary in concepts):
            raise ValueError("subject summary concepts must belong to its subject")
        for field_name in ("mastery_score", "confidence"):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"summary {field_name} must be in [0, 1]")
        if self.evidence_count < 0:
            raise ValueError("summary evidence count must not be negative")

        counts = tuple((GapStatus(status), count) for status, count in self.gap_status_counts)
        if any(count < 0 for _, count in counts):
            raise ValueError("summary gap counts must not be negative")
        if len({status for status, _ in counts}) != len(counts):
            raise ValueError("summary gap statuses must be unique")

        object.__setattr__(self, "concepts", concepts)
        object.__setattr__(self, "gap_status_counts", counts)


class BuildSubjectSummary:
    """Build a subject summary from provider-neutral learner evidence ports."""

    def __init__(
        self,
        *,
        concepts: ConceptCatalogPort,
        attempts: AttemptPort,
        mastery_states: MasteryStatePort,
    ) -> None:
        self._concepts = concepts
        self._attempts = attempts
        self._mastery_states = mastery_states

    def execute(self, command: BuildSubjectSummaryCommand) -> SubjectSummary:
        """Return aggregate metrics while preserving concept evidence drill-down."""

        concepts = tuple(
            sorted(
                self._concepts.list_concepts(command.subject_id),
                key=lambda concept: concept.id,
            )
        )
        if not concepts:
            raise ValueError(f"unknown subject or empty concept graph: {command.subject_id}")

        history = self._attempts.list_attempts(command.learner_id)
        attempts_by_concept = {
            concept.id: tuple(history.get(concept.id, ()))
            for concept in concepts
            if history.get(concept.id)
        }
        existing_states = dict(self._mastery_states.get_states(command.learner_id))
        engine = LearningEngine(concepts)
        concept_summaries: list[ConceptSummary] = []

        for concept in concepts:
            evidence = attempts_by_concept.get(concept.id, ())
            if evidence:
                outcome = engine.evaluate(
                    focus_concept_id=concept.id,
                    attempts_by_concept=attempts_by_concept,
                    existing_states=existing_states,
                )
                concept_summaries.append(
                    ConceptSummary(
                        concept=concept,
                        mastery_state=outcome.mastery_state,
                        gap_status=outcome.gap_status,
                        recommendation=outcome.recommendation,
                        evidence=evidence,
                    )
                )
                continue

            concept_summaries.append(
                ConceptSummary(
                    concept=concept,
                    mastery_state=existing_states.get(concept.id),
                    gap_status=GapStatus.NOT_ENOUGH_EVIDENCE,
                    recommendation=None,
                    evidence=(),
                )
            )

        states = tuple(
            summary.mastery_state
            for summary in concept_summaries
            if summary.mastery_state is not None
        )
        mastery_score = self._average(state.score for state in states)
        confidence = self._average(state.confidence for state in states)
        evidence_count = sum(len(summary.evidence) for summary in concept_summaries)
        gap_counts = Counter(summary.gap_status for summary in concept_summaries)

        return SubjectSummary(
            learner_id=command.learner_id,
            subject_id=command.subject_id,
            concepts=tuple(concept_summaries),
            mastery_score=mastery_score,
            confidence=confidence,
            evidence_count=evidence_count,
            gap_status_counts=tuple(
                (status, gap_counts.get(status, 0)) for status in GapStatus
            ),
        )

    @staticmethod
    def _average(values: Iterable[float]) -> float:
        values_tuple = tuple(values)
        if not values_tuple:
            return 0.0
        return round(sum(values_tuple) / len(values_tuple), 4)
