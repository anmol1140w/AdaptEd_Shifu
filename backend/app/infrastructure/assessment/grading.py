"""Deterministic assessment grading adapter for local and test execution."""

from __future__ import annotations

from ...application.ports.assessment import (
    AssessmentGradingError,
    GradingResult,
)
from ...domain.entities.learning import AssessmentItem


class DeterministicAssessmentGrader:
    """Compare normalized answers against the approved catalog answer."""

    def grade(self, *, item: AssessmentItem, answer: str) -> GradingResult:
        if not item.approved:
            raise AssessmentGradingError(
                f"cannot grade an unapproved assessment item: {item.id}"
            )
        if not isinstance(answer, str) or not answer.strip():
            raise AssessmentGradingError("learner answer must not be empty")

        is_correct = self._normalize(answer) == self._normalize(item.answer)
        return GradingResult(
            is_correct=is_correct,
            misconception=None if is_correct else item.misconception_tag,
        )

    @staticmethod
    def _normalize(answer: str) -> str:
        """Make whitespace and letter casing irrelevant for simple answer checks."""

        return "".join(answer.casefold().split())
