"""Behavior tests for tutor and weak-area quiz v1 contract mapping."""

from __future__ import annotations

import json
import unittest

from backend.app.application.ports.ai import QuizRequest, TutorMode, TutorRequest
from backend.app.application.use_cases.generate_weak_area_quiz import WeakAreaQuizResult
from backend.app.application.use_cases.provide_tutor_support import TutorSupportResult
from backend.app.domain.entities.learning import Concept, Difficulty
from backend.app.infrastructure.ai.llm import (
    DeterministicQuizGenerator,
    DeterministicTutorGenerator,
)
from backend.app.schemas.learning_support_v1 import (
    LearningSupportContractError,
    parse_tutor_request,
    parse_weak_area_quiz_request,
    tutor_response,
    weak_area_quiz_response,
)


class LearningSupportSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concept = Concept(
            id="ALG-DIST-01",
            subject_id="maths-9",
            name="Distributive property",
        )

    def test_tutor_request_maps_and_rejects_unknown_mode(self) -> None:
        command = parse_tutor_request(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
                "concept_id": "ALG-DIST-01",
                "mode": "hint",
                "misconception": "negative sign not distributed",
            }
        )

        self.assertEqual(command.mode, TutorMode.HINT)
        self.assertEqual(command.learner_id, "learner-riya")

        with self.assertRaisesRegex(LearningSupportContractError, "mode"):
            parse_tutor_request(
                {
                    "contract_version": "v1",
                    "learner_id": "learner-riya",
                    "subject_id": "maths-9",
                    "concept_id": "ALG-DIST-01",
                    "mode": "solve_it",
                }
            )

    def test_quiz_request_maps_defaults_and_rejects_bad_count(self) -> None:
        command = parse_weak_area_quiz_request(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
                "concept_id": "ALG-DIST-01",
                "difficulty": "medium",
            }
        )

        self.assertEqual(command.difficulty, Difficulty.MEDIUM)
        self.assertEqual(command.item_count, 3)
        self.assertTrue(command.include_transfer)

        with self.assertRaisesRegex(LearningSupportContractError, "item_count"):
            parse_weak_area_quiz_request(
                {
                    "contract_version": "v1",
                    "learner_id": "learner-riya",
                    "subject_id": "maths-9",
                    "concept_id": "ALG-DIST-01",
                    "difficulty": "medium",
                    "item_count": 6,
                }
            )

    def test_tutor_response_is_json_safe(self) -> None:
        draft = DeterministicTutorGenerator().generate(
            request=TutorRequest(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode=TutorMode.HINT,
            ),
            sources=(),
        )
        result = TutorSupportResult(
            learner_id="learner-riya",
            subject_id="maths-9",
            concept_id=self.concept.id,
            concept=self.concept,
            draft=draft,
            fallback_used=True,
            audit_event_id="ai-audit-1",
        )

        response = tutor_response(result)

        self.assertEqual(json.loads(json.dumps(response)), response)
        self.assertFalse(response["answer_revealed"])
        self.assertIn("check_question", response)

    def test_quiz_response_redacts_internal_answers(self) -> None:
        request = QuizRequest(
            learner_id="learner-riya",
            subject_id="maths-9",
            concept_id=self.concept.id,
            difficulty=Difficulty.MEDIUM,
            item_count=2,
        )
        draft = DeterministicQuizGenerator().generate(request=request, sources=())
        result = WeakAreaQuizResult(
            learner_id="learner-riya",
            subject_id="maths-9",
            concept_id=self.concept.id,
            concept=self.concept,
            draft=draft,
            fallback_used=True,
            audit_event_id="ai-audit-2",
        )

        response = weak_area_quiz_response(result)

        self.assertEqual(json.loads(json.dumps(response)), response)
        self.assertEqual(len(response["items"]), 2)
        self.assertTrue(all("answer" not in item for item in response["items"]))


if __name__ == "__main__":
    unittest.main()
