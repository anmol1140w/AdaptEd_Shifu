"""Build an evidence-backed, teacher-review intervention queue."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ...domain.entities.learning import (
    AttemptEvidence,
    Concept,
    GapStatus,
    MasteryState,
    Recommendation,
)
from ...domain.services.learning_engine import LearningEngine
from ..ports.assessment import ConceptCatalogPort
from ..ports.learning import (
    AttemptPort,
    LearnerRosterPort,
    MasteryStatePort,
    RecommendationPort,
)


class InterventionPriority(str, Enum):
    """Human-readable queue priority used by teacher clients."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class BuildInterventionQueueCommand:
    """Input for one subject and an optionally restricted learner group."""

    subject_id: str
    learner_ids: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if not self.subject_id.strip():
            raise ValueError("subject id must not be empty")
        if self.learner_ids is not None:
            learner_ids = tuple(self.learner_ids)
            if any(not learner_id.strip() for learner_id in learner_ids):
                raise ValueError("learner IDs must not be empty")
            if len(set(learner_ids)) != len(learner_ids):
                raise ValueError("learner IDs must be unique")
            object.__setattr__(self, "learner_ids", learner_ids)


@dataclass(frozen=True, slots=True)
class TeacherIntervention:
    """One actionable learner/concept candidate with traceable evidence."""

    id: str
    learner_id: str
    subject_id: str
    concept: Concept
    priority: InterventionPriority
    gap_status: GapStatus
    recommendation: Recommendation
    mastery_state: MasteryState | None
    evidence: tuple[AttemptEvidence, ...]
    repeated_error_count: int
    average_hint_count: float

    def __post_init__(self) -> None:
        for field_name in ("id", "learner_id", "subject_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"intervention {field_name} must not be empty")
        if self.concept.subject_id != self.subject_id:
            raise ValueError("intervention concept must belong to subject")
        if self.recommendation.target_concept_id != self.concept.id:
            raise ValueError("intervention recommendation must target its concept")
        if self.mastery_state is not None and self.mastery_state.concept_id != self.concept.id:
            raise ValueError("intervention mastery must match its concept")
        evidence = tuple(self.evidence)
        if any(attempt.id not in self.recommendation.evidence_ids for attempt in evidence):
            raise ValueError("intervention evidence must be referenced by recommendation")
        if self.repeated_error_count < 0:
            raise ValueError("intervention repeated error count must not be negative")
        if self.average_hint_count < 0:
            raise ValueError("intervention average hint count must not be negative")
        if not isinstance(self.priority, InterventionPriority):
            object.__setattr__(self, "priority", InterventionPriority(self.priority))
        if not isinstance(self.gap_status, GapStatus):
            object.__setattr__(self, "gap_status", GapStatus(self.gap_status))
        object.__setattr__(self, "evidence", evidence)


@dataclass(frozen=True, slots=True)
class InterventionQueue:
    """Stable queue result for one subject."""

    subject_id: str
    interventions: tuple[TeacherIntervention, ...]

    def __post_init__(self) -> None:
        if not self.subject_id.strip():
            raise ValueError("queue subject id must not be empty")
        interventions = tuple(self.interventions)
        ids = [intervention.id for intervention in interventions]
        if len(ids) != len(set(ids)):
            raise ValueError("intervention IDs must be unique")
        object.__setattr__(self, "interventions", interventions)


class BuildInterventionQueue:
    """Rank evidence-backed candidates without making an autonomous decision."""

    _PRIORITY_ORDER = {
        InterventionPriority.HIGH: 3,
        InterventionPriority.MEDIUM: 2,
        InterventionPriority.LOW: 1,
    }

    def __init__(
        self,
        *,
        learners: LearnerRosterPort,
        concepts: ConceptCatalogPort,
        attempts: AttemptPort,
        mastery_states: MasteryStatePort,
        recommendations: RecommendationPort,
    ) -> None:
        self._learners = learners
        self._concepts = concepts
        self._attempts = attempts
        self._mastery_states = mastery_states
        self._recommendations = recommendations

    def execute(self, command: BuildInterventionQueueCommand) -> InterventionQueue:
        """Return ranked open candidates for the requested subject."""

        concepts = tuple(
            sorted(self._concepts.list_concepts(command.subject_id), key=lambda concept: concept.id)
        )
        if not concepts:
            raise ValueError(f"unknown subject or empty concept graph: {command.subject_id}")
        concept_map = {concept.id: concept for concept in concepts}
        learner_ids = (
            command.learner_ids
            if command.learner_ids is not None
            else tuple(self._learners.list_learner_ids(command.subject_id))
        )

        candidates: dict[tuple[str, str], TeacherIntervention] = {}
        engine = LearningEngine(concepts)
        for learner_id in sorted(set(learner_ids)):
            history = self._attempts.list_attempts(learner_id)
            attempts_by_concept = {
                concept_id: tuple(attempts)
                for concept_id, attempts in history.items()
                if concept_id in concept_map and attempts
            }
            if not attempts_by_concept:
                continue
            states = dict(self._mastery_states.get_states(learner_id))
            latest = self._recommendations.latest(learner_id)
            for focus_concept_id in sorted(attempts_by_concept):
                outcome = engine.evaluate(
                    focus_concept_id=focus_concept_id,
                    attempts_by_concept=attempts_by_concept,
                    existing_states=states,
                )
                recommendation = outcome.recommendation
                if latest is not None and latest.target_concept_id == recommendation.target_concept_id:
                    recommendation = latest
                if not self._needs_intervention(outcome.gap_status, recommendation):
                    continue

                target = concept_map.get(recommendation.target_concept_id)
                if target is None:
                    continue
                evidence = self._evidence_for(recommendation, history)
                if not evidence:
                    continue
                target_state = states.get(target.id)
                if target_state is None and target.id in attempts_by_concept:
                    target_state = LearningEngine.calculate_mastery(
                        target,
                        attempts_by_concept[target.id],
                    )
                priority = self._priority(
                    gap_status=outcome.gap_status,
                    recommendation=recommendation,
                    evidence=evidence,
                )
                intervention = TeacherIntervention(
                    id=f"intervention-{learner_id}-{target.id}",
                    learner_id=learner_id,
                    subject_id=command.subject_id,
                    concept=target,
                    priority=priority,
                    gap_status=outcome.gap_status,
                    recommendation=recommendation,
                    mastery_state=target_state,
                    evidence=evidence,
                    repeated_error_count=self._repeated_error_count(evidence),
                    average_hint_count=round(
                        sum(attempt.hint_count for attempt in evidence) / len(evidence),
                        4,
                    ),
                )
                key = (learner_id, target.id)
                current = candidates.get(key)
                if current is None or self._sort_key(intervention) < self._sort_key(current):
                    candidates[key] = intervention

        ordered = tuple(sorted(candidates.values(), key=self._sort_key))
        return InterventionQueue(subject_id=command.subject_id, interventions=ordered)

    @staticmethod
    def _needs_intervention(gap_status: GapStatus, recommendation: Recommendation) -> bool:
        return recommendation.teacher_review_required or gap_status in {
            GapStatus.PREREQUISITE_BLOCKED,
            GapStatus.NEEDS_SUPPORT,
            GapStatus.FRAGILE,
        }

    @staticmethod
    def _evidence_for(
        recommendation: Recommendation,
        history: dict[str, tuple[AttemptEvidence, ...]],
    ) -> tuple[AttemptEvidence, ...]:
        evidence_by_id = {
            attempt.id: attempt
            for attempts in history.values()
            for attempt in attempts
        }
        return tuple(
            evidence_by_id[evidence_id]
            for evidence_id in recommendation.evidence_ids
            if evidence_id in evidence_by_id
        )

    @classmethod
    def _priority(
        cls,
        *,
        gap_status: GapStatus,
        recommendation: Recommendation,
        evidence: tuple[AttemptEvidence, ...],
    ) -> InterventionPriority:
        repeated_errors = cls._repeated_error_count(evidence)
        average_hints = sum(attempt.hint_count for attempt in evidence) / len(evidence)
        if gap_status is GapStatus.PREREQUISITE_BLOCKED or (
            recommendation.teacher_review_required
            and repeated_errors >= 2
            and average_hints >= 1.0
        ):
            return InterventionPriority.HIGH
        if recommendation.teacher_review_required or gap_status is GapStatus.NEEDS_SUPPORT:
            return InterventionPriority.MEDIUM
        return InterventionPriority.LOW

    @classmethod
    def _sort_key(cls, intervention: TeacherIntervention) -> tuple[object, ...]:
        confidence = (
            intervention.mastery_state.confidence
            if intervention.mastery_state is not None
            else 0.0
        )
        return (
            -cls._PRIORITY_ORDER[intervention.priority],
            -(intervention.gap_status is GapStatus.PREREQUISITE_BLOCKED),
            -intervention.repeated_error_count,
            -intervention.average_hint_count,
            -len(intervention.evidence),
            confidence,
            intervention.learner_id,
            intervention.concept.id,
        )

    @staticmethod
    def _repeated_error_count(evidence: tuple[AttemptEvidence, ...]) -> int:
        return sum(1 for attempt in evidence if not attempt.is_correct)
