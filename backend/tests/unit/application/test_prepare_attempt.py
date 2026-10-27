"""Tests for preparing raw answers as graded attempt evidence."""

from __future__ import annotations

import unittest

from backend.app.application.ports.assessment import AssessmentGradingError, GradingResult
from backend.app.application.use_cases.prepare_attempt import (
    PrepareAttempt,
    PrepareAttemptCommand,
)
from backend.app.domain.entities.learning import AssessmentItem, Difficulty


class InMemoryItems:
    def __init__(self, items: list[AssessmentItem]) -> None:
        self.items = {item.id: item for item in items}

    def get_item(self, item_id: str) -> AssessmentItem | None:
        return self.items.get(item_id)

    def list_items(self, subject_id: str) -> tuple[AssessmentItem, ...]:
        return tuple(item for item in self.items.values() if item.subject_id == subject_id)


class RecordingGrader:
    def __init__(self, result: GradingResult | None = None) -> None:
        self.result = result or GradingResult(is_correct=True)
        self.calls: list[tuple[str, str]] = []

    def grade(self, *, item: AssessmentItem, answer: str) -> GradingResult:
        self.calls.append((item.id, answer))
        return self.result


class FailingGrader:
    def grade(self, *, item: AssessmentItem, answer: str) -> GradingResult:
        raise AssessmentGradingError("grading provider unavailable")


class PrepareAttemptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = AssessmentItem(
            id="item-eq",
            subject_id="maths-9",
            concept_id="ALG-EQ-02",
            difficulty=Difficulty.HARD,
            question="Solve 2x + 3 = 11.",
            answer="x = 4",
            misconception_tag="isolated the constant before dividing",
        )
        self.catalog = InMemoryItems([self.item])

    def test_correct_answer_becomes_evidence_with_item_difficulty(self) -> None:
        grader = RecordingGrader(GradingResult(is_correct=True))
        use_case = PrepareAttempt(items=self.catalog, grader=grader)

        evidence = use_case.execute(self._command(answer="x = 4"))

        self.assertTrue(evidence.is_correct)
        self.assertEqual(evidence.difficulty, Difficulty.HARD)
        self.assertEqual(evidence.item_id, self.item.id)
        self.assertEqual(evidence.response_ms, 1200)
        self.assertEqual(evidence.hint_count, 1)
        self.assertEqual(grader.calls, [(self.item.id, "x = 4")])

    def test_incorrect_answer_preserves_grader_misconception(self) -> None:
        grader = RecordingGrader(
            GradingResult(
                is_correct=False,
                misconception="isolated the constant before dividing",
            )
        )
        use_case = PrepareAttempt(items=self.catalog, grader=grader)

        evidence = use_case.execute(self._command(answer="x = 8"))

        self.assertFalse(evidence.is_correct)
        self.assertEqual(
            evidence.misconception,
            "isolated the constant before dividing",
        )

    def test_unknown_item_is_rejected_before_grader_call(self) -> None:
        grader = RecordingGrader()
        use_case = PrepareAttempt(items=self.catalog, grader=grader)

        with self.assertRaisesRegex(ValueError, "unknown assessment item"):
            use_case.execute(self._command(item_id="item-missing"))

        self.assertEqual(grader.calls, [])

    def test_unapproved_item_is_rejected_before_grader_call(self) -> None:
        unapproved = AssessmentItem(
            id="item-draft",
            subject_id="maths-9",
            concept_id="ALG-EQ-02",
            difficulty=Difficulty.MEDIUM,
            question="Draft question.",
            answer="x = 2",
            approved=False,
        )
        catalog = InMemoryItems([unapproved])
        grader = RecordingGrader()

        with self.assertRaisesRegex(ValueError, "not approved"):
            PrepareAttempt(items=catalog, grader=grader).execute(
                self._command(item_id=unapproved.id)
            )

        self.assertEqual(grader.calls, [])

    def test_item_concept_mismatch_is_rejected_before_grader_call(self) -> None:
        grader = RecordingGrader()

        with self.assertRaisesRegex(ValueError, "does not match submitted concept"):
            PrepareAttempt(items=self.catalog, grader=grader).execute(
                self._command(concept_id="ALG-DIST-01")
            )

        self.assertEqual(grader.calls, [])

    def test_grading_failure_is_propagated_without_creating_evidence(self) -> None:
        use_case = PrepareAttempt(items=self.catalog, grader=FailingGrader())

        with self.assertRaisesRegex(AssessmentGradingError, "unavailable"):
            use_case.execute(self._command())

    def _command(
        self,
        *,
        answer: str = "x = 4",
        item_id: str = "item-eq",
        concept_id: str = "ALG-EQ-02",
    ) -> PrepareAttemptCommand:
        return PrepareAttemptCommand(
            session_id="session-1",
            learner_id="learner-riya",
            attempt_id="attempt-1",
            item_id=item_id,
            concept_id=concept_id,
            answer=answer,
            response_ms=1200,
            hint_count=1,
            confidence_signal=0.4,
        )


if __name__ == "__main__":
    unittest.main()
