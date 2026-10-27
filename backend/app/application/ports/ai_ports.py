"""AdaptEd AI Subsystem Application Ports and Core Data Contracts.

Defines provider-neutral boundaries and schema contracts for:
- Language Model Client (LLMPort)
- Knowledge Retriever (RetrieverPort)
- Grounded RAG Tutor (TutorPort)
- Weak-Area Quiz Generator (QuizGeneratorPort)
- Output & Safety Validator (ValidatorPort)
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T", bound="BaseSchema")


class ValidationError(ValueError):
    """Raised when structured AI input or output fails schema validation."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[str]] = None,
        safety_flags: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]
        self.safety_flags = safety_flags or []


@dataclass
class BaseSchema:
    """Base schema providing dictionary/JSON serialization and Pydantic-compatible helpers."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a clean Python dictionary."""
        return asdict(self)

    def dict(self) -> Dict[str, Any]:
        """Pydantic v1 compatibility alias for to_dict."""
        return self.to_dict()

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """Pydantic v2 compatibility alias for to_dict."""
        return self.to_dict()

    def to_json(self) -> str:
        """Serialize model to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def model_dump_json(self, **kwargs: Any) -> str:
        """Pydantic v2 compatibility alias for JSON serialization."""
        return self.to_json()

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Construct and validate model instance from dictionary."""
        raise NotImplementedError

    @classmethod
    def model_validate(cls: Type[T], obj: Any) -> T:
        """Pydantic v2 compatibility alias for from_dict."""
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, str):
            try:
                data = json.loads(obj)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Invalid JSON string: {exc}") from exc
        elif isinstance(obj, dict):
            data = obj
        else:
            raise ValidationError(f"Expected dict or JSON string, got {type(obj).__name__}")
        return cls.from_dict(data)

    @classmethod
    def parse_obj(cls: Type[T], obj: Any) -> T:
        """Pydantic v1 compatibility alias."""
        return cls.model_validate(obj)


@dataclass
class RetrievedChunk(BaseSchema):
    """Approved curriculum lesson chunk or worked example retrieved for grounded tutoring."""

    id: str
    text: str
    concept_id: str = ""
    source_id: Optional[str] = None
    title: Optional[str] = None
    score: float = 1.0
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("RetrievedChunk must have a non-empty 'id'")
        if not self.text:
            raise ValidationError("RetrievedChunk must have non-empty 'text'")
        if self.source_id is None:
            self.source_id = self.id
        self.score = float(self.score)
        if not isinstance(self.tags, list):
            self.tags = list(self.tags) if self.tags else []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RetrievedChunk:
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict for RetrievedChunk, got {type(data).__name__}")
        return cls(
            id=str(data.get("id", "")).strip(),
            text=str(data.get("text", "")).strip(),
            concept_id=str(data.get("concept_id", "")).strip(),
            source_id=str(data.get("source_id", data.get("id", ""))).strip(),
            title=data.get("title"),
            score=float(data.get("score", 1.0)),
            tags=list(data.get("tags", [])),
        )


@dataclass
class TutorRequest(BaseSchema):
    """Input payload to the grounded RAG tutor."""

    grade: int = 9
    subject: str = "Mathematics"
    concept: str = ""
    concept_id: str = ""
    learner_attempt: str = ""
    requested_mode: str = "hint"
    retrieved_sources: List[RetrievedChunk] = field(default_factory=list)

    def __post_init__(self) -> None:
        valid_modes = {"hint", "explanation", "check_question"}
        if self.requested_mode not in valid_modes:
            raise ValidationError(
                f"Invalid requested_mode: '{self.requested_mode}'. Must be one of {sorted(valid_modes)}"
            )
        normalized_sources: List[RetrievedChunk] = []
        for src in self.retrieved_sources:
            if isinstance(src, RetrievedChunk):
                normalized_sources.append(src)
            elif isinstance(src, dict):
                normalized_sources.append(RetrievedChunk.from_dict(src))
            else:
                raise ValidationError(f"Invalid retrieved source object type: {type(src).__name__}")
        self.retrieved_sources = normalized_sources

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TutorRequest:
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict for TutorRequest, got {type(data).__name__}")
        raw_sources = data.get("retrieved_sources", [])
        return cls(
            grade=int(data.get("grade", 9)),
            subject=str(data.get("subject", "Mathematics")),
            concept=str(data.get("concept", "")),
            concept_id=str(data.get("concept_id", "")),
            learner_attempt=str(data.get("learner_attempt", "")),
            requested_mode=str(data.get("requested_mode", "hint")),
            retrieved_sources=raw_sources,
        )


@dataclass
class TutorResponse(BaseSchema):
    """Structured, verified response from the grounded RAG tutor."""

    mode: str
    message: str
    check_question: str
    source_ids: List[str] = field(default_factory=list)
    confidence: str = "high"
    needs_teacher_review: bool = False
    safety_flags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        valid_modes = {"hint", "explanation", "check_question"}
        if self.mode not in valid_modes:
            raise ValidationError(f"Invalid mode '{self.mode}'. Must be one of {sorted(valid_modes)}")
        valid_confidence = {"high", "medium", "low"}
        if self.confidence not in valid_confidence:
            raise ValidationError(
                f"Invalid confidence '{self.confidence}'. Must be one of {sorted(valid_confidence)}"
            )
        if not isinstance(self.source_ids, list):
            self.source_ids = list(self.source_ids)
        if not isinstance(self.safety_flags, list):
            self.safety_flags = list(self.safety_flags)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TutorResponse:
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict for TutorResponse, got {type(data).__name__}")
        return cls(
            mode=str(data.get("mode", "hint")).strip(),
            message=str(data.get("message", "")).strip(),
            check_question=str(data.get("check_question", "")).strip(),
            source_ids=[str(s).strip() for s in data.get("source_ids", [])],
            confidence=str(data.get("confidence", "high")).strip(),
            needs_teacher_review=bool(data.get("needs_teacher_review", False)),
            safety_flags=[str(f).strip() for f in data.get("safety_flags", [])],
        )


@dataclass
class QuizRequest(BaseSchema):
    """Request to generate targeted quiz items targeting a learner's weak area."""

    learner_id: str
    grade: int = 9
    subject: str = "Mathematics"
    concept_id: str = ""
    misconception: str = ""
    difficulty: str = "medium"
    num_items: int = 3
    requested_representations: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if not self.learner_id:
            raise ValidationError("learner_id cannot be empty")
        if not self.concept_id:
            raise ValidationError("concept_id cannot be empty")
        valid_difficulties = {"easy", "medium", "hard", "scaffolded", "transfer"}
        if self.difficulty not in valid_difficulties:
            raise ValidationError(
                f"Invalid difficulty '{self.difficulty}'. Must be one of {sorted(valid_difficulties)}"
            )
        if self.num_items < 1:
            raise ValidationError("num_items must be >= 1")
        if self.requested_representations is None:
            self.requested_representations = ["symbolic", "error_analysis", "verbal", "transfer"]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QuizRequest:
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict for QuizRequest, got {type(data).__name__}")
        return cls(
            learner_id=str(data.get("learner_id", "")).strip(),
            grade=int(data.get("grade", 9)),
            subject=str(data.get("subject", "Mathematics")),
            concept_id=str(data.get("concept_id", "")).strip(),
            misconception=str(data.get("misconception", "")).strip(),
            difficulty=str(data.get("difficulty", "medium")).strip(),
            num_items=int(data.get("num_items", 3)),
            requested_representations=data.get("requested_representations"),
        )


@dataclass
class QuizItem(BaseSchema):
    """Individual assessment item within a generated quiz draft."""

    id: str
    representation: str
    question: str
    answer_type: str
    difficulty: str = "medium"
    options: Optional[List[str]] = None
    answer: str = ""
    explanation: str = ""
    source_id: Optional[str] = None
    concept_id: Optional[str] = None
    misconception_tag: Optional[str] = None

    def __post_init__(self) -> None:
        valid_reps = {"symbolic", "error_analysis", "verbal", "visual", "transfer"}
        if self.representation not in valid_reps:
            raise ValidationError(
                f"Invalid representation '{self.representation}'. Must be one of {sorted(valid_reps)}"
            )
        valid_types = {"expression", "choice", "numeric", "explanation"}
        if self.answer_type not in valid_types:
            raise ValidationError(
                f"Invalid answer_type '{self.answer_type}'. Must be one of {sorted(valid_types)}"
            )
        if self.answer_type == "choice":
            if not self.options or len(self.options) < 2:
                raise ValidationError("Items with answer_type='choice' must have at least 2 options")
            if self.answer and self.answer not in self.options:
                raise ValidationError(f"Answer '{self.answer}' must be present in choices: {self.options}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QuizItem:
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict for QuizItem, got {type(data).__name__}")
        options = data.get("options")
        if options is not None:
            options = [str(o) for o in options]
        return cls(
            id=str(data.get("id", "")).strip(),
            representation=str(data.get("representation", "symbolic")).strip(),
            question=str(data.get("question", "")).strip(),
            answer_type=str(data.get("answer_type", "expression")).strip(),
            difficulty=str(data.get("difficulty", "medium")).strip(),
            options=options,
            answer=str(data.get("answer", "")).strip(),
            explanation=str(data.get("explanation", "")).strip(),
            source_id=data.get("source_id"),
            concept_id=data.get("concept_id"),
            misconception_tag=data.get("misconception_tag"),
        )


@dataclass
class QuizResponse(BaseSchema):
    """Complete response payload for a generated weak-area quiz."""

    quiz_id: str
    concept_id: str
    target_misconception: str
    difficulty: str
    items: List[QuizItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        normalized_items: List[QuizItem] = []
        for itm in self.items:
            if isinstance(itm, QuizItem):
                normalized_items.append(itm)
            elif isinstance(itm, dict):
                normalized_items.append(QuizItem.from_dict(itm))
            else:
                raise ValidationError(f"Invalid item type in QuizResponse: {type(itm).__name__}")
        self.items = normalized_items

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QuizResponse:
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict for QuizResponse, got {type(data).__name__}")
        raw_items = data.get("items", [])
        return cls(
            quiz_id=str(data.get("quiz_id", "")).strip(),
            concept_id=str(data.get("concept_id", "")).strip(),
            target_misconception=str(data.get("target_misconception", "")).strip(),
            difficulty=str(data.get("difficulty", "medium")).strip(),
            items=raw_items,
        )


@dataclass
class ValidationResult(BaseSchema):
    """Outcome of safety, pedagogical, or schema validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    safety_flags: List[str] = field(default_factory=list)
    sanitized_response: Optional[Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationResult:
        return cls(
            is_valid=bool(data.get("is_valid", False)),
            errors=list(data.get("errors", [])),
            safety_flags=list(data.get("safety_flags", [])),
            sanitized_response=data.get("sanitized_response"),
        )


# =====================================================================
# Application Ports (Abstract Interfaces)
# =====================================================================

class LLMPort(ABC):
    """Abstract port for language model interaction."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Generate unstructured text completion."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured completion adhering to schema type."""
        pass


class RetrieverPort(ABC):
    """Abstract port for deterministic offline content retrieval."""

    @abstractmethod
    def retrieve(self, concept_id: str, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        """Retrieve approved content chunks deterministically matching concept and query."""
        pass


class TutorPort(ABC):
    """Abstract port for grounded RAG tutoring."""

    @abstractmethod
    def respond(self, request: TutorRequest) -> TutorResponse:
        """Process learner attempt and return validated, grounded tutor response."""
        pass


class QuizGeneratorPort(ABC):
    """Abstract port for targeted weak-area quiz generation."""

    @abstractmethod
    def generate_quiz(self, request: QuizRequest) -> QuizResponse:
        """Generate structured quiz items targeting learner misconception."""
        pass


class ValidatorPort(ABC):
    """Abstract port for pedagogical and safety validation."""

    @abstractmethod
    def validate_tutor_response(
        self, response: TutorResponse, request: TutorRequest
    ) -> ValidationResult:
        """Validate tutor response against grounding, anti-spoiler, and safety rules."""
        pass

    @abstractmethod
    def validate_quiz_response(
        self, response: QuizResponse, request: QuizRequest
    ) -> ValidationResult:
        """Validate quiz response against representation, option, and schema rules."""
        pass
