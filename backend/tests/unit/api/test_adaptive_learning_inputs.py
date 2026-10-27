"""Validation tests for adaptive assessment and teammate score ingestion."""

from __future__ import annotations

import unittest
import importlib.util
from pathlib import Path

from pydantic import ValidationError

_route_path = Path(__file__).resolve().parents[3] / "src/backend/app/api/v1/learning_contracts.py"
_route_spec = importlib.util.spec_from_file_location("adapted_learning_contracts", _route_path)
assert _route_spec and _route_spec.loader
_contracts = importlib.util.module_from_spec(_route_spec)
_route_spec.loader.exec_module(_contracts)
ExternalQuizScoreImport = _contracts.ExternalQuizScoreImport
TopicScoreInput = _contracts.TopicScoreInput


class AdaptiveLearningInputTests(unittest.TestCase):
    def test_external_scores_accept_partial_marks_and_optional_stable_question_id(self) -> None:
        payload = ExternalQuizScoreImport.model_validate({
            "source_system": "quiz-module",
            "source_event_id": "attempt-123",
            "student_id": "student-456",
            "quiz_id": "quiz-789",
            "subject": "physics",
            "class_level": 11,
            "questions": [{
                "concept_id": "phy-11-motion",
                "question": "A body starts at rest. Find its displacement after 2 s.",
                "score": 1.5,
                "max_score": 2,
            }],
        })

        self.assertEqual(payload.questions[0].score, 1.5)
        self.assertIsNone(payload.questions[0].question_id)

    def test_external_scores_reject_score_above_maximum(self) -> None:
        with self.assertRaises(ValidationError):
            ExternalQuizScoreImport.model_validate({
                "source_system": "quiz-module", "source_event_id": "attempt-123",
                "student_id": "student-456", "quiz_id": "quiz-789",
                "subject": "chemistry", "class_level": 12,
                "questions": [{"concept_id": "chem-12", "question": "Balance the reaction.", "score": 3, "max_score": 2}],
            })

    def test_topic_scores_require_bounded_mastery_and_trend(self) -> None:
        score = TopicScoreInput.model_validate({
            "topic": "Kinematics", "attempts": 2, "correct": 1,
            "accuracy": 0.5, "mastery_score": 0.61, "confidence": 0.5, "trend": "stable",
        })
        self.assertEqual(score.trend, "stable")
        with self.assertRaises(ValidationError):
            TopicScoreInput.model_validate({
                "topic": "Kinematics", "attempts": 2, "correct": 1,
                "accuracy": 1.2, "mastery_score": 0.61, "confidence": 0.5, "trend": "stable",
            })


if __name__ == "__main__":
    unittest.main()
