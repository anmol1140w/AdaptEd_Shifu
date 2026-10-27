"""Immutable entities used by the provider-independent learning domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Difficulty(str, Enum):
    """Difficulty labels used by the adaptive policy."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Trend(str, Enum):
    """Direction of recent evidence for a concept."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class GapStatus(str, Enum):
    """Human-readable mastery state used by recommendations and views."""

    NOT_ENOUGH_EVIDENCE = "not_enough_evidence"
    PREREQUISITE_BLOCKED = "prerequisite_blocked"
    NEEDS_SUPPORT = "needs_support"
    DEVELOPING = "developing"
    FRAGILE = "fragile"
    SECURE = "secure"


class ActionType(str, Enum):
    """Next learning actions produced by the deterministic policy."""

    BASELINE_CHECK = "baseline_check"
    PREREQUISITE_SUPPORT = "prerequisite_support"
    TARGETED_PRACTICE = "targeted_practice"
    TRANSFER_PRACTICE = "transfer_practice"


class AssessmentSessionStatus(str, Enum):
    """Lifecycle state for an assessment session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Concept:
    """A concept in the subject prerequisite graph."""

    id: str
    subject_id: str
    name: str
    prerequisite_ids: tuple[str, ...] = ()
    mastery_threshold: float = 0.72

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("concept id must not be empty")
        if not self.subject_id.strip():
            raise ValueError("subject id must not be empty")
        if not self.name.strip():
            raise ValueError("concept name must not be empty")
        if not 0.0 < self.mastery_threshold <= 1.0:
            raise ValueError("mastery threshold must be in (0, 1]")

        prerequisites = tuple(self.prerequisite_ids)
        if self.id in prerequisites:
            raise ValueError("a concept cannot depend on itself")
        object.__setattr__(self, "prerequisite_ids", prerequisites)


@dataclass(frozen=True, slots=True)
class AssessmentItem:
    """Teacher-approved item that can be served in an assessment."""

    id: str
    subject_id: str
    concept_id: str
    difficulty: Difficulty
    question: str
    answer: str
    misconception_tag: str | None = None
    source_id: str | None = None
    approved: bool = True

    def __post_init__(self) -> None:
        for field_name in ("id", "subject_id", "concept_id", "question", "answer"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not isinstance(self.difficulty, Difficulty):
            object.__setattr__(self, "difficulty", Difficulty(self.difficulty))
        if not isinstance(self.approved, bool):
            raise ValueError("approved must be a boolean")


@dataclass(frozen=True, slots=True)
class AssessmentSession:
    """A learner's assessment context before attempts are submitted."""

    id: str
    learner_id: str
    subject_id: str
    current_concept_id: str
    status: AssessmentSessionStatus = AssessmentSessionStatus.ACTIVE

    def __post_init__(self) -> None:
        for field_name in ("id", "learner_id", "subject_id", "current_concept_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not isinstance(self.status, AssessmentSessionStatus):
            object.__setattr__(self, "status", AssessmentSessionStatus(self.status))


@dataclass(frozen=True, slots=True)
class AttemptEvidence:
    """A single learner interaction used as evidence for a concept."""

    id: str
    item_id: str
    concept_id: str
    is_correct: bool
    difficulty: Difficulty
    hint_count: int = 0
    response_ms: int | None = None
    confidence_signal: float | None = None
    misconception: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("attempt id must not be empty")
        if not self.item_id.strip():
            raise ValueError("attempt item id must not be empty")
        if not self.concept_id.strip():
            raise ValueError("attempt concept id must not be empty")
        if not isinstance(self.is_correct, bool):
            raise ValueError("is_correct must be a boolean")
        if not isinstance(self.difficulty, Difficulty):
            object.__setattr__(self, "difficulty", Difficulty(self.difficulty))
        if self.hint_count < 0:
            raise ValueError("hint count must not be negative")
        if self.response_ms is not None and self.response_ms < 0:
            raise ValueError("response time must not be negative")
        if self.confidence_signal is not None and not 0.0 <= self.confidence_signal <= 1.0:
            raise ValueError("confidence signal must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class MasteryState:
    """Explainable mastery estimate for one learner and one concept."""

    concept_id: str
    score: float
    confidence: float
    evidence_count: int
    trend: Trend
    likely_misconception: str | None
    recent_correctness: float
    independence_score: float

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("mastery concept id must not be empty")
        for field_name in (
            "score",
            "confidence",
            "recent_correctness",
            "independence_score",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be in [0, 1]")
        if self.evidence_count < 0:
            raise ValueError("evidence count must not be negative")
        if not isinstance(self.trend, Trend):
            object.__setattr__(self, "trend", Trend(self.trend))


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A next action with an inspectable reason and supporting evidence."""

    action_type: ActionType
    target_concept_id: str
    reason: str
    evidence_ids: tuple[str, ...]
    teacher_review_required: bool = False

    def __post_init__(self) -> None:
        if not self.target_concept_id.strip():
            raise ValueError("recommendation target concept id must not be empty")
        if not self.reason.strip():
            raise ValueError("recommendation reason must not be empty")
        if not isinstance(self.action_type, ActionType):
            object.__setattr__(self, "action_type", ActionType(self.action_type))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class LearningOutcome:
    """Result returned by the domain after evaluating learner evidence."""

    mastery_state: MasteryState
    gap_status: GapStatus
    recommendation: Recommendation

    def __post_init__(self) -> None:
        if not isinstance(self.gap_status, GapStatus):
            object.__setattr__(self, "gap_status", GapStatus(self.gap_status))
