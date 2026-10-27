"""Behavior tests for the first learning-domain slice."""

from __future__ import annotations

import unittest

from backend.app.domain.entities.learning import (
    ActionType,
    AttemptEvidence,
    Concept,
    Difficulty,
    GapStatus,
    Trend,
)
from backend.app.domain.services.learning_engine import LearningEngine


class LearningEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.variables = Concept(
            id="ALG-VAR-01",
            subject_id="maths-9",
            name="Variables and expressions",
        )
        self.distributive = Concept(
            id="ALG-DIST-01",
            subject_id="maths-9",
            name="Distributive property",
            prerequisite_ids=(self.variables.id,),
        )
        self.two_step = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
            prerequisite_ids=(self.distributive.id,),
        )
        self.engine = LearningEngine(
            concepts=(self.variables, self.distributive, self.two_step)
        )

    def test_riya_gets_prerequisite_support_and_teacher_review(self) -> None:
        variable_attempts = [
            self._attempt("var-1", self.variables, correct=True),
            self._attempt("var-2", self.variables, correct=True),
        ]
        distributive_attempts = [
            self._attempt(
                "dist-1",
                self.distributive,
                correct=False,
                hints=2,
                misconception="negative sign not distributed",
            ),
            self._attempt(
                "dist-2",
                self.distributive,
                correct=False,
                hints=2,
                misconception="negative sign not distributed",
            ),
        ]
        two_step_attempts = [
            self._attempt("eq-1", self.two_step, correct=False, hints=1),
        ]

        outcome = self.engine.evaluate(
            focus_concept_id=self.two_step.id,
            attempts_by_concept={
                self.variables.id: variable_attempts,
                self.distributive.id: distributive_attempts,
                self.two_step.id: two_step_attempts,
            },
        )

        self.assertEqual(outcome.gap_status, GapStatus.PREREQUISITE_BLOCKED)
        self.assertEqual(
            outcome.recommendation.action_type,
            ActionType.PREREQUISITE_SUPPORT,
        )
        self.assertEqual(
            outcome.recommendation.target_concept_id,
            self.distributive.id,
        )
        self.assertTrue(outcome.recommendation.teacher_review_required)
        self.assertEqual(
            outcome.recommendation.evidence_ids,
            ("eq-1", "dist-1", "dist-2"),
        )

    def test_arjun_gets_transfer_practice_after_independent_success(self) -> None:
        attempts = [
            self._attempt("eq-1", self.two_step, correct=True),
            self._attempt("eq-2", self.two_step, correct=True),
            self._attempt("eq-3", self.two_step, correct=True, difficulty=Difficulty.HARD),
            self._attempt("eq-4", self.two_step, correct=True, difficulty=Difficulty.HARD),
        ]

        outcome = self.engine.evaluate(
            focus_concept_id=self.two_step.id,
            attempts_by_concept={self.two_step.id: attempts},
        )

        self.assertEqual(outcome.gap_status, GapStatus.SECURE)
        self.assertEqual(
            outcome.recommendation.action_type,
            ActionType.TRANSFER_PRACTICE,
        )
        self.assertEqual(outcome.mastery_state.trend, Trend.STABLE)
        self.assertGreaterEqual(outcome.mastery_state.confidence, 0.75)
        self.assertGreaterEqual(outcome.mastery_state.score, self.two_step.mastery_threshold)

    def test_low_evidence_is_not_declared_secure(self) -> None:
        attempt = self._attempt("eq-1", self.two_step, correct=True)

        outcome = self.engine.evaluate(
            focus_concept_id=self.two_step.id,
            attempts_by_concept={self.two_step.id: [attempt]},
        )

        self.assertEqual(outcome.gap_status, GapStatus.NOT_ENOUGH_EVIDENCE)
        self.assertEqual(
            outcome.recommendation.action_type,
            ActionType.BASELINE_CHECK,
        )
        self.assertEqual(
            outcome.mastery_state.trend,
            Trend.INSUFFICIENT_EVIDENCE,
        )

    def test_invalid_attempt_mapping_is_rejected(self) -> None:
        attempt = self._attempt("eq-1", self.two_step, correct=True)

        with self.assertRaises(ValueError):
            self.engine.evaluate(
                focus_concept_id=self.two_step.id,
                attempts_by_concept={self.distributive.id: [attempt]},
            )

    def test_negative_hint_count_is_rejected_at_the_evidence_boundary(self) -> None:
        with self.assertRaises(ValueError):
            AttemptEvidence(
                id="invalid-1",
                item_id="item-invalid",
                concept_id=self.two_step.id,
                is_correct=False,
                difficulty=Difficulty.MEDIUM,
                hint_count=-1,
            )

    @staticmethod
    def _attempt(
        attempt_id: str,
        concept: Concept,
        *,
        correct: bool,
        hints: int = 0,
        difficulty: Difficulty = Difficulty.MEDIUM,
        misconception: str | None = None,
    ) -> AttemptEvidence:
        return AttemptEvidence(
            id=attempt_id,
            item_id=f"item-{attempt_id}",
            concept_id=concept.id,
            is_correct=correct,
            difficulty=difficulty,
            hint_count=hints,
            misconception=misconception,
        )


if __name__ == "__main__":
    unittest.main()
