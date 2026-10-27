"""Validated request models for adaptive learner evidence and tutor context."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class ExternalQuizQuestion(BaseModel):
    question_id: str | None = Field(default=None, min_length=1, max_length=180)
    concept_id: str = Field(min_length=3, max_length=180)
    question: str = Field(min_length=3, max_length=5000)
    response: str = Field(default="", max_length=5000)
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    time_taken: int = Field(default=0, ge=0, le=86400)


class ExternalQuizScoreImport(BaseModel):
    source_system: str = Field(min_length=2, max_length=100)
    source_event_id: str = Field(min_length=1, max_length=180)
    student_id: str = Field(min_length=1, max_length=180)
    quiz_id: str = Field(min_length=1, max_length=180)
    subject: str = Field(pattern="^(physics|chemistry|mathematics)$")
    class_level: int = Field(ge=11, le=12)
    attempted_at: datetime | None = None
    questions: list[ExternalQuizQuestion] = Field(min_length=1, max_length=200)

    @field_validator("questions")
    @classmethod
    def _valid_scores(cls, value: list[ExternalQuizQuestion]) -> list[ExternalQuizQuestion]:
        for question in value:
            if question.score > question.max_score:
                raise ValueError("score must not exceed max_score")
        return value

    @field_validator("attempted_at")
    @classmethod
    def _require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("attempted_at must include a timezone")
        return value


class TopicScoreInput(BaseModel):
    topic: str = Field(min_length=1, max_length=180)
    attempts: int = Field(ge=0, le=10000)
    correct: int = Field(ge=0, le=10000)
    accuracy: float = Field(ge=0, le=1)
    mastery_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    trend: str = Field(pattern="^(insufficient_evidence|improving|stable|declining)$")

    @model_validator(mode="after")
    def _validate_attempt_counts(self) -> "TopicScoreInput":
        if self.correct > self.attempts:
            raise ValueError("correct must not exceed attempts")
        return self
