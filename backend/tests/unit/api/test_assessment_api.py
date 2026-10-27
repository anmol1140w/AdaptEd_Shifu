"""Tests for the framework-independent v1 assessment route adapter."""

from __future__ import annotations

import unittest

from backend.app.api.v1.routes.assessment import (
    AssessmentApi,
    LearnerRequestContext,
)
from backend.app.application.assessment_facade import AssessmentFacadeError
from backend.app.application.ports.assessment import AssessmentGradingError
from backend.app.schemas.assessment_v1 import AssessmentContractError


class FakeAssessmentFacade:
    def __init__(self) -> None:
        self.start_calls: list[dict[str, object]] = []
        self.submit_calls: list[dict[str, object]] = []
        self.summary_calls: list[dict[str, object]] = []
        self.start_result: dict[str, object] = {
            "contract_version": "v1",
            "session": {"id": "session-1"},
        }
        self.submit_result: dict[str, object] = {
            "contract_version": "v1",
            "recommendation": {"action_type": "transfer_practice"},
        }
        self.summary_result: dict[str, object] = {
            "contract_version": "v1",
            "summary": {"evidence_count": 0},
        }
        self.start_error: Exception | None = None
        self.submit_error: Exception | None = None

    def start(self, payload: dict[str, object]) -> dict[str, object]:
        self.start_calls.append(payload)
        if self.start_error is not None:
            raise self.start_error
        return self.start_result

    def submit(self, payload: dict[str, object]) -> dict[str, object]:
        self.submit_calls.append(payload)
        if self.submit_error is not None:
            raise self.submit_error
        return self.submit_result

    def summary(self, payload: dict[str, object]) -> dict[str, object]:
        self.summary_calls.append(payload)
        return self.summary_result


class AssessmentApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.facade = FakeAssessmentFacade()
        self.api = AssessmentApi(facade=self.facade)  # type: ignore[arg-type]
        self.context = LearnerRequestContext(principal_id="learner-riya")

    def test_start_returns_created_response_from_facade(self) -> None:
        payload = {
            "contract_version": "v1",
            "learner_id": "learner-riya",
            "subject_id": "maths-9",
        }

        response = self.api.start(payload, context=self.context)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.body, self.facade.start_result)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(self.facade.start_calls, [payload])

    def test_submit_returns_ok_response_from_facade(self) -> None:
        payload = {
            "contract_version": "v1",
            "learner_id": "learner-riya",
            "session_id": "session-1",
            "attempt": {"id": "attempt-1"},
        }

        response = self.api.submit(payload, context=self.context)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, self.facade.submit_result)
        self.assertEqual(self.facade.submit_calls, [payload])

    def test_summary_returns_ok_response_from_facade(self) -> None:
        payload = self._start_payload()

        response = self.api.summary(payload, context=self.context)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, self.facade.summary_result)
        self.assertEqual(self.facade.summary_calls, [payload])

    def test_missing_context_returns_unauthenticated_without_facade_call(self) -> None:
        response = self.api.start(self._start_payload(), context=None)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body["error"]["code"], "authentication_required")
        self.assertEqual(self.facade.start_calls, [])

    def test_non_learner_context_returns_forbidden(self) -> None:
        response = self.api.start(
            self._start_payload(),
            context=LearnerRequestContext(principal_id="teacher-1", role="teacher"),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body["error"]["code"], "learner_role_required")
        self.assertEqual(self.facade.start_calls, [])

    def test_payload_learner_mismatch_returns_forbidden(self) -> None:
        response = self.api.start(
            self._start_payload(learner_id="learner-arjun"),
            context=self.context,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body["error"]["code"], "learner_context_mismatch")
        self.assertEqual(self.facade.start_calls, [])

    def test_contract_error_maps_to_bad_request(self) -> None:
        self.facade.start_error = AssessmentContractError("missing subject_id")

        response = self.api.start(self._start_payload(), context=self.context)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body["error"]["code"], "invalid_assessment_contract")
        self.assertEqual(response.body["error"]["message"], "missing subject_id")

    def test_grading_error_maps_to_service_unavailable(self) -> None:
        self.facade.submit_error = AssessmentGradingError("provider unavailable")

        response = self.api.submit(self._submit_payload(), context=self.context)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.body["error"]["code"],
            "assessment_grading_unavailable",
        )
        self.assertNotIn("provider unavailable", response.body["error"]["message"])

    def test_facade_context_error_maps_to_internal_response_error(self) -> None:
        self.facade.submit_error = AssessmentFacadeError("missing response context")

        response = self.api.submit(self._submit_payload(), context=self.context)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.body["error"]["code"],
            "assessment_response_unavailable",
        )
        self.assertNotIn("missing response context", response.body["error"]["message"])

    def test_application_rejection_maps_to_unprocessable_entity(self) -> None:
        self.facade.submit_error = ValueError("unknown assessment session: session-missing")

        response = self.api.submit(self._submit_payload(), context=self.context)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.body["error"]["code"], "assessment_request_rejected")
        self.assertIn("unknown assessment session", response.body["error"]["message"])

    @staticmethod
    def _start_payload(*, learner_id: str = "learner-riya") -> dict[str, object]:
        return {
            "contract_version": "v1",
            "learner_id": learner_id,
            "subject_id": "maths-9",
        }

    @staticmethod
    def _submit_payload() -> dict[str, object]:
        return {
            "contract_version": "v1",
            "learner_id": "learner-riya",
            "session_id": "session-1",
            "attempt": {"id": "attempt-1"},
        }


if __name__ == "__main__":
    unittest.main()
