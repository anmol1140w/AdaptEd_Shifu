"""Provider-neutral boundaries for retrieval, generation, validation and audit."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from ...domain.entities.learning import Difficulty


class AIIntegrationError(RuntimeError):
    """Raised when an AI integration cannot safely produce a result."""


class AIValidationError(AIIntegrationError):
    """Raised when generated content fails the application safety boundary."""


class TutorMode(str, Enum):
    """Supported tutor behaviors exposed to the application."""

    HINT = "hint"
    EXPLANATION = "explanation"
    CHECK_QUESTION = "check_question"


class QuizRepresentation(str, Enum):
    """Representation types allowed for generated weak-area items."""

    SYMBOLIC = "symbolic"
    VERBAL = "verbal"
    STORY = "story"


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    """Context used to retrieve approved learning content."""

    subject_id: str
    concept_id: str
    query: str
    misconception: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("subject_id", "concept_id", "query"):
            value = getattr(self, field_name)
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.misconception is not None and not self.misconception.strip():
            raise ValueError("misconception must not be empty when provided")


@dataclass(frozen=True, slots=True)
class RetrievedSource:
    """One approved source chunk available to a generated response."""

    source_id: str
    subject_id: str
    concept_id: str
    title: str
    text: str
    confidence: float = 1.0
    approved: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "subject_id",
            "concept_id",
            "title",
            "text",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("source confidence must be in [0, 1]")
        if not isinstance(self.approved, bool):
            raise ValueError("source approval must be a boolean")


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Retrieved source context and aggregate retrieval confidence."""

    sources: tuple[RetrievedSource, ...] = ()
    confidence: float = 0.0

    def __post_init__(self) -> None:
        sources = tuple(self.sources)
        source_ids = [source.source_id for source in sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("retrieved source IDs must be unique")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("retrieval confidence must be in [0, 1]")
        object.__setattr__(self, "sources", sources)


class RetrievalPort(Protocol):
    """Retrieve approved source chunks for a learning request."""

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Return approved source context or an empty low-confidence result."""
        ...


@dataclass(frozen=True, slots=True)
class TutorRequest:
    """Learner and learning context supplied to a tutor generator."""

    learner_id: str
    subject_id: str
    concept_id: str
    mode: TutorMode
    learner_answer: str | None = None
    misconception: str | None = None
    learner_level: str = "class_9"

    def __post_init__(self) -> None:
        for field_name in ("learner_id", "subject_id", "concept_id", "learner_level"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not isinstance(self.mode, TutorMode):
            object.__setattr__(self, "mode", TutorMode(self.mode))
        if self.learner_answer is not None and not self.learner_answer.strip():
            raise ValueError("learner answer must not be empty when provided")
        if self.misconception is not None and not self.misconception.strip():
            raise ValueError("misconception must not be empty when provided")


@dataclass(frozen=True, slots=True)
class TutorDraft:
    """Structured tutor output before validation and contract mapping."""

    mode: TutorMode
    message: str
    check_question: str
    source_ids: tuple[str, ...]
    confidence: float
    teacher_review_required: bool
    answer_revealed: bool = False
    provider: str = "unknown"

    def __post_init__(self) -> None:
        if not isinstance(self.mode, TutorMode):
            object.__setattr__(self, "mode", TutorMode(self.mode))
        if not self.message.strip():
            raise ValueError("tutor message must not be empty")
        if not self.check_question.strip():
            raise ValueError("tutor check question must not be empty")
        source_ids = tuple(self.source_ids)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("tutor source IDs must be unique")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("tutor confidence must be in [0, 1]")
        if not isinstance(self.teacher_review_required, bool):
            raise ValueError("tutor teacher-review flag must be a boolean")
        if not isinstance(self.answer_revealed, bool):
            raise ValueError("tutor answer-revealed flag must be a boolean")
        if not self.provider.strip():
            raise ValueError("tutor provider must not be empty")
        object.__setattr__(self, "source_ids", source_ids)


class TutorGenerationPort(Protocol):
    """Generate a structured tutor response from approved source context."""

    def generate(
        self,
        *,
        request: TutorRequest,
        sources: Sequence[RetrievedSource],
    ) -> TutorDraft:
        """Return a structured tutor draft without changing learning policy."""
        ...


@dataclass(frozen=True, slots=True)
class QuizRequest:
    """Learner and weak-area context supplied to a quiz generator."""

    learner_id: str
    subject_id: str
    concept_id: str
    difficulty: Difficulty
    item_count: int = 3
    misconception: str | None = None
    include_transfer: bool = True

    def __post_init__(self) -> None:
        for field_name in ("learner_id", "subject_id", "concept_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not isinstance(self.difficulty, Difficulty):
            object.__setattr__(self, "difficulty", Difficulty(self.difficulty))
        if not isinstance(self.item_count, int) or isinstance(self.item_count, bool):
            raise ValueError("quiz item count must be an integer")
        if not 1 <= self.item_count <= 5:
            raise ValueError("quiz item count must be in [1, 5]")
        if self.misconception is not None and not self.misconception.strip():
            raise ValueError("misconception must not be empty when provided")
        if not isinstance(self.include_transfer, bool):
            raise ValueError("include_transfer must be a boolean")


@dataclass(frozen=True, slots=True)
class QuizItemDraft:
    """Generated quiz item kept internal until answer redaction."""

    id: str
    subject_id: str
    concept_id: str
    difficulty: Difficulty
    question: str
    answer: str
    representation: QuizRepresentation
    source_ids: tuple[str, ...]
    is_transfer: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "subject_id",
            "concept_id",
            "question",
            "answer",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"quiz item {field_name} must not be empty")
        if not isinstance(self.difficulty, Difficulty):
            object.__setattr__(self, "difficulty", Difficulty(self.difficulty))
        if not isinstance(self.representation, QuizRepresentation):
            object.__setattr__(
                self,
                "representation",
                QuizRepresentation(self.representation),
            )
        source_ids = tuple(self.source_ids)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("quiz item source IDs must be unique")
        if not isinstance(self.is_transfer, bool):
            raise ValueError("quiz item transfer flag must be a boolean")
        object.__setattr__(self, "source_ids", source_ids)


@dataclass(frozen=True, slots=True)
class QuizDraft:
    """Structured generated quiz before validation and answer redaction."""

    items: tuple[QuizItemDraft, ...]
    source_ids: tuple[str, ...]
    confidence: float
    teacher_review_required: bool
    provider: str = "unknown"

    def __post_init__(self) -> None:
        items = tuple(self.items)
        if not items:
            raise ValueError("quiz must contain at least one item")
        item_ids = [item.id for item in items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("quiz item IDs must be unique")
        source_ids = tuple(self.source_ids)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("quiz source IDs must be unique")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("quiz confidence must be in [0, 1]")
        if not isinstance(self.teacher_review_required, bool):
            raise ValueError("quiz teacher-review flag must be a boolean")
        if not self.provider.strip():
            raise ValueError("quiz provider must not be empty")
        object.__setattr__(self, "items", items)
        object.__setattr__(self, "source_ids", source_ids)


class QuizGenerationPort(Protocol):
    """Generate structured weak-area quiz items from approved source context."""

    def generate(
        self,
        *,
        request: QuizRequest,
        sources: Sequence[RetrievedSource],
    ) -> QuizDraft:
        """Return quiz items without changing mastery or progression policy."""
        ...


class GeneratedContentValidatorPort(Protocol):
    """Validate generated tutor and quiz output before it reaches a learner."""

    def validate_tutor(
        self,
        *,
        request: TutorRequest,
        draft: TutorDraft,
        sources: Sequence[RetrievedSource],
    ) -> None:
        """Raise ``AIValidationError`` when tutor output is unsafe or ungrounded."""
        ...

    def validate_quiz(
        self,
        *,
        request: QuizRequest,
        draft: QuizDraft,
        sources: Sequence[RetrievedSource],
    ) -> None:
        """Raise ``AIValidationError`` when quiz output is unsafe or misaligned."""
        ...


@dataclass(frozen=True, slots=True)
class AIAuditEvent:
    """Decision and generation metadata for a persistence adapter."""

    event_type: str
    learner_id: str
    subject_id: str
    concept_id: str
    provider: str
    fallback_used: bool
    source_ids: tuple[str, ...]
    validation_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "event_type",
            "learner_id",
            "subject_id",
            "concept_id",
            "provider",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"audit {field_name} must not be empty")
        if not isinstance(self.fallback_used, bool):
            raise ValueError("audit fallback flag must be a boolean")
        object.__setattr__(self, "source_ids", tuple(self.source_ids))
        object.__setattr__(self, "validation_flags", tuple(self.validation_flags))


class AIAuditPort(Protocol):
    """Record model/source/decision information without coupling use cases to storage."""

    def record(self, event: AIAuditEvent) -> str:
        """Persist an audit event and return its stable identifier."""
        ...
