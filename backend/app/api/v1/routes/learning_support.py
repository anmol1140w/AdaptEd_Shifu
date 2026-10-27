"""Thin v1 route adapter for tutor and weak-area quiz support."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable

from ....application.learning_support_facade import LearningSupportFacade
from ....application.ports.ai import AIIntegrationError
from ....schemas.learning_support_v1 import LearningSupportContractError
from .assessment import AssessmentApiResponse, LearnerRequestContext


@dataclass(frozen=True, slots=True)
class LearningSupportApi:
    """Adapt trusted learner context and payloads to support use cases."""

    facade: LearningSupportFacade

    TUTOR_PATH = "/api/v1/tutor/responses"
    WEAK_AREA_QUIZ_PATH = "/api/v1/quizzes/weak-area"

    def tutor(
        self,
        payload: Mapping[str, object],
        *,
        context: LearnerRequestContext | None,
    ) -> AssessmentApiResponse:
        """Handle a tutor-support request."""

        return self._run(
            payload=payload,
            context=context,
            operation=self.facade.tutor,
        )

    def weak_area_quiz(
        self,
        payload: Mapping[str, object],
        *,
        context: LearnerRequestContext | None,
    ) -> AssessmentApiResponse:
        """Handle a weak-area quiz request."""

        return self._run(
            payload=payload,
            context=context,
            operation=self.facade.weak_area_quiz,
        )

    def _run(
        self,
        *,
        payload: Mapping[str, object],
        context: LearnerRequestContext | None,
        operation: Callable[[Mapping[str, object]], dict[str, Any]],
    ) -> AssessmentApiResponse:
        authorization_error = self._authorize(payload=payload, context=context)
        if authorization_error is not None:
            return authorization_error
        try:
            return AssessmentApiResponse(status_code=200, body=operation(payload))
        except LearningSupportContractError as exc:
            return AssessmentApiResponse(
                status_code=400,
                body={
                    "error": {
                        "code": "invalid_learning_support_contract",
                        "message": str(exc),
                    }
                },
            )
        except AIIntegrationError:
            return AssessmentApiResponse(
                status_code=503,
                body={
                    "error": {
                        "code": "learning_support_unavailable",
                        "message": "Learning support is unavailable right now.",
                    }
                },
            )
        except ValueError as exc:
            return AssessmentApiResponse(
                status_code=422,
                body={
                    "error": {
                        "code": "learning_support_request_rejected",
                        "message": str(exc),
                    }
                },
            )

    @staticmethod
    def _authorize(
        *,
        payload: Mapping[str, object],
        context: LearnerRequestContext | None,
    ) -> AssessmentApiResponse | None:
        if context is None:
            return AssessmentApiResponse(
                status_code=401,
                body={
                    "error": {
                        "code": "authentication_required",
                        "message": "Learner authentication is required.",
                    }
                },
            )
        if context.role != "learner":
            return AssessmentApiResponse(
                status_code=403,
                body={
                    "error": {
                        "code": "learner_role_required",
                        "message": "A learner role is required for learning support actions.",
                    }
                },
            )
        requested_learner = payload.get("learner_id") if isinstance(payload, Mapping) else None
        if isinstance(requested_learner, str) and requested_learner != context.principal_id:
            return AssessmentApiResponse(
                status_code=403,
                body={
                    "error": {
                        "code": "learner_context_mismatch",
                        "message": "The request learner does not match the authenticated learner.",
                    }
                },
            )
        return None
