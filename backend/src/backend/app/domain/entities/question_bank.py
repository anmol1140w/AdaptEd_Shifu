"""Question-bank values and independently managed learning metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from .learning import Difficulty


class BloomLevel(IntEnum):
    REMEMBER = 1
    UNDERSTAND = 2
    APPLY = 3
    ANALYZE = 4
    EVALUATE = 5
    CREATE = 6

    @property
    def code(self) -> str:
        return f"BT{int(self)}"


@dataclass(frozen=True, slots=True)
class QuestionDraft:
    """Normalized question row received after file decoding."""

    question: str
    question_type: str
    subject: str
    topic: str
    correct_answer: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    difficulty: Difficulty | None = None
    bloom_level: BloomLevel | None = None
    marks: float | None = None
    time_seconds: int | None = None
    explanation: str | None = None

    def __post_init__(self) -> None:
        for name in ("question", "question_type", "subject", "topic"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        allowed_types = {"mcq", "numerical", "short_answer", "descriptive", "coding"}
        if self.question_type not in allowed_types:
            raise ValueError(f"question_type must be one of {', '.join(sorted(allowed_types))}")
        if self.question_type == "mcq":
            options = [self.fields.get(f"option_{letter}") for letter in "abcd"]
            if sum(isinstance(value, str) and bool(value.strip()) for value in options) < 2:
                raise ValueError("mcq questions require at least two options")
            if self.fields.get("correct_option") is None and not self.correct_answer.strip():
                raise ValueError("mcq questions require correct_answer or correct_option")
        elif self.question_type in {"numerical", "short_answer"} and not self.correct_answer.strip():
            raise ValueError(f"{self.question_type} questions require correct_answer")
        elif self.question_type == "descriptive" and not (self.correct_answer.strip() or self.fields.get("rubric") or self.fields.get("marking_rubric")):
            raise ValueError("descriptive questions require correct_answer or rubric")
        elif self.question_type == "coding" and not (self.correct_answer.strip() or self.fields.get("test_cases")):
            raise ValueError("coding questions require correct_answer or test_cases")
        if self.difficulty is not None and not isinstance(self.difficulty, Difficulty):
            object.__setattr__(self, "difficulty", Difficulty(str(self.difficulty).lower()))
        if self.bloom_level is not None and not isinstance(self.bloom_level, BloomLevel):
            object.__setattr__(self, "bloom_level", BloomLevel(int(self.bloom_level)))
        if self.marks is not None and (isinstance(self.marks, bool) or self.marks <= 0):
            raise ValueError("marks must be a positive number")
        if self.time_seconds is not None and (isinstance(self.time_seconds, bool) or self.time_seconds <= 0):
            raise ValueError("time_seconds must be a positive integer")


@dataclass(frozen=True, slots=True)
class ClassifiedQuestion:
    """Question plus machine suggestions and teacher-controlled final values."""

    question_id: str
    draft: QuestionDraft
    suggested_bloom_level: BloomLevel
    bloom_confidence: float
    bloom_reason: str
    bloom_source: str
    bloom_teacher_verified: bool
    bloom_level: BloomLevel
    suggested_difficulty: Difficulty
    difficulty_source: str
    difficulty_teacher_verified: bool
    difficulty: Difficulty
