"""Tests for the framework-independent teacher queue route adapter."""

from __future__ import annotations

import unittest

from backend.app.api.v1.routes.teacher_interventions import (
    TeacherInterventionApi,
    TeacherRequestContext,
)


class FakeTeacherFacade:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def queue(self, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append(payload)
        return {"contract_version": "v1", "interventions": []}


class TeacherInterventionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.facade = FakeTeacherFacade()
        self.api = TeacherInterventionApi(facade=self.facade)  # type: ignore[arg-type]

    def test_teacher_group_is_injected_when_request_omits_filter(self) -> None:
        response = self.api.queue(
            {"contract_version": "v1", "subject_id": "maths-9"},
            context=TeacherRequestContext(
                principal_id="teacher-1",
                allowed_learner_ids=("learner-riya",),
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.facade.calls[0]["learner_ids"], ["learner-riya"])

    def test_teacher_cannot_request_an_outside_learner(self) -> None:
        response = self.api.queue(
            {
                "contract_version": "v1",
                "subject_id": "maths-9",
                "learner_ids": ["learner-arjun"],
            },
            context=TeacherRequestContext(
                principal_id="teacher-1",
                allowed_learner_ids=("learner-riya",),
            ),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body["error"]["code"], "learner_group_forbidden")
        self.assertEqual(self.facade.calls, [])

    def test_non_teacher_context_is_rejected(self) -> None:
        response = self.api.queue(
            {"contract_version": "v1", "subject_id": "maths-9"},
            context=TeacherRequestContext(principal_id="learner-riya", role="learner"),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body["error"]["code"], "teacher_role_required")


if __name__ == "__main__":
    unittest.main()
