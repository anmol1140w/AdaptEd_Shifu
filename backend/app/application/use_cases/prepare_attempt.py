"""Prepare raw assessment input as domain evidence after grading."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.learning import AttemptEvidence
from ..ports.assessment import AssessmentGraderPort, ItemCatalogPort


@dataclass(frozen=True, slots=True)
class PrepareAttemptCommand:
    """Validated learner input that still needs answer grading."""

    session_id: str
    learner_id: str
    attempt_id: str
    item_id: str
    concept_id: str
    answer: str
    response_ms: int | None = None
    hint_count: int = 0
    confidence_signal: float | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "session_id",
            "learner_id",
            "attempt_id",
            "item_id",
            "concept_id",
            "answer",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.hint_count, int) or isinstance(self.hint_count, bool):
            raise ValueError("hint count must be an integer")
        if self.hint_count < 0:
            raise ValueError("hint count must not be negative")
        if self.response_ms is not None:
            if not isinstance(self.response_ms, int) or isinstance(self.response_ms, bool):
                raise ValueError("response time must be an integer or null")
            if self.response_ms < 0:
                raise ValueError("response time must not be negative")
        if self.confidence_signal is not None:
            if isinstance(self.confidence_signal, bool) or not isinstance(
                self.confidence_signal,
                (int, float),
            ):
                raise ValueError("confidence signal must be a number or null")
            if not 0.0 <= self.confidence_signal <= 1.0:
                raise ValueError("confidence signal must be in [0, 1]")


class PrepareAttempt:
    """Load an approved item, grade its answer, and create domain evidence."""

    def __init__(
        self,
        *,
        items: ItemCatalogPort,
        grader: AssessmentGraderPort,
    ) -> None:
        self._items = items
        self._grader = grader

    def execute(self, command: PrepareAttemptCommand) -> AttemptEvidence:
        """Return evidence or fail before the learning use case can persist it."""

        item = self._items.get_item(command.item_id)
        if item is None:
            raise ValueError(f"unknown assessment item: {command.item_id}")
        if not item.approved:
            raise ValueError(f"assessment item is not approved: {command.item_id}")
        if item.concept_id != command.concept_id:
            raise ValueError("assessment item does not match submitted concept")

        grading = self._grader.grade(item=item, answer=command.answer)
        return AttemptEvidence(
            id=command.attempt_id,
            item_id=item.id,
            concept_id=command.concept_id,
            is_correct=grading.is_correct,
            difficulty=item.difficulty,
            hint_count=command.hint_count,
            response_ms=command.response_ms,
            confidence_signal=command.confidence_signal,
            misconception=grading.misconception,
        )
