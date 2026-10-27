"""Tests for deterministic assessment grading."""

from __future__ import annotations

import unittest

from backend.app.application.ports.assessment import AssessmentGradingError
from backend.app.domain.entities.learning import AssessmentItem, Difficulty
from backend.app.infrastructure.assessment.grading import DeterministicAssessmentGrader


class DeterministicAssessmentGraderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grader = DeterministicAssessmentGrader()
        self.item = AssessmentItem(
            id="item-eq",
            subject_id="maths-9",
            concept_id="ALG-EQ-02",
            difficulty=Difficulty.MEDIUM,
            question="Solve x + 3 = 7.",
            answer="x = 4",
            misconception_tag="did not isolate the constant",
        )

    def test_grader_ignores_case_and_whitespace_for_simple_answers(self) -> None:
        result = self.grader.grade(item=self.item, answer=" X = 4 ")

        self.assertTrue(result.is_correct)
        self.assertIsNone(result.misconception)

    def test_grader_returns_seeded_misconception_for_incorrect_answer(self) -> None:
        result = self.grader.grade(item=self.item, answer="x = 5")

        self.assertFalse(result.is_correct)
        self.assertEqual(result.misconception, "did not isolate the constant")

    def test_empty_answer_is_a_grading_failure(self) -> None:
        with self.assertRaisesRegex(AssessmentGradingError, "must not be empty"):
            self.grader.grade(item=self.item, answer=" ")

    def test_unapproved_item_is_a_grading_failure(self) -> None:
        draft = AssessmentItem(
            id="item-draft",
            subject_id="maths-9",
            concept_id="ALG-EQ-02",
            difficulty=Difficulty.MEDIUM,
            question="Draft question.",
            answer="x = 1",
            approved=False,
        )

        with self.assertRaisesRegex(AssessmentGradingError, "unapproved"):
            self.grader.grade(item=draft, answer="x = 1")


if __name__ == "__main__":
    unittest.main()
