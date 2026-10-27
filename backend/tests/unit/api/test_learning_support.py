"""Tests for the framework-independent tutor and quiz route adapter."""

from __future__ import annotations

import unittest

from backend.app.api.v1.routes.assessment import LearnerRequestContext
from backend.app.api.v1.routes.learning_support import LearningSupportApi


class FakeLearningSupportFacade:
    def __init__(self) -> None:
        self.tutor_calls: list[dict[str, object]] = []
        self.quiz_calls: list[dict[str, object]] = []

    def tutor(self, payload: dict[str, object]) -> dict[str, object]:
        self.tutor_calls.append(payload)
        return {"contract_version": "v1", "mode": "hint"}

    def weak_area_quiz(self, payload: dict[str, object]) -> dict[str, object]:
        self.quiz_calls.append(payload)
        return {"contract_version": "v1", "items": []}


class LearningSupportApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.facade = FakeLearningSupportFacade()
        self.api = LearningSupportApi(facade=self.facade)  # type: ignore[arg-type]
        self.context = LearnerRequestContext(principal_id="learner-riya")

    def test_tutor_delegates_with_authenticated_context(self) -> None:
        payload = {
            "contract_version": "v1",
            "learner_id": "learner-riya",
            "subject_id": "maths-9",
            "concept_id": "ALG-DIST-01",
            "mode": "hint",
        }

        response = self.api.tutor(payload, context=self.context)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["mode"], "hint")
        self.assertEqual(self.facade.tutor_calls, [payload])

    def test_quiz_rejects_missing_authentication_before_facade_call(self) -> None:
        response = self.api.weak_area_quiz(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
                "concept_id": "ALG-DIST-01",
                "difficulty": "medium",
            },
            context=None,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body["error"]["code"], "authentication_required")
        self.assertEqual(self.facade.quiz_calls, [])

    def test_tutor_rejects_identity_mismatch(self) -> None:
        response = self.api.tutor(
            {
                "contract_version": "v1",
                "learner_id": "learner-arjun",
                "subject_id": "maths-9",
                "concept_id": "ALG-DIST-01",
                "mode": "hint",
            },
            context=self.context,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body["error"]["code"], "learner_context_mismatch")
        self.assertEqual(self.facade.tutor_calls, [])


if __name__ == "__main__":
    unittest.main()
