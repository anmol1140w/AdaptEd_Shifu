"""Thin v1 assessment route adapter around the application facade."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable

from ....application.assessment_facade import (
    AssessmentFacade,
    AssessmentFacadeError,
)
from ....application.ports.assessment import AssessmentGradingError
from ....schemas.assessment_v1 import AssessmentContractError


@dataclass(frozen=True, slots=True)
class LearnerRequestContext:
    """Trusted identity context supplied by the future authentication layer."""

    principal_id: str
    role: str = "learner"

    def __post_init__(self) -> None:
        if not self.principal_id.strip():
            raise ValueError("request principal id must not be empty")
        if not self.role.strip():
            raise ValueError("request role must not be empty")


@dataclass(frozen=True, slots=True)
class AssessmentApiResponse:
    """Framework-neutral HTTP-like response for a v1 assessment route."""

    status_code: int
    body: dict[str, Any]
    headers: Mapping[str, str] = field(
        default_factory=lambda: {"content-type": "application/json"}
    )


class AssessmentApi:
    """Adapt learner request context and payloads to ``AssessmentFacade``."""

    START_PATH = "/api/v1/assessments/start"
    SUBMIT_PATH = "/api/v1/assessments/attempts"
    SUMMARY_PATH = "/api/v1/assessments/summary"

    def __init__(self, *, facade: AssessmentFacade) -> None:
        self._facade = facade

    def start(
        self,
        payload: Mapping[str, object],
        *,
        context: LearnerRequestContext | None,
    ) -> AssessmentApiResponse:
        """Handle the future start-assessment endpoint."""

        return self._run(
            payload=payload,
            context=context,
            operation=self._facade.start,
            success_status=201,
        )

    def submit(
        self,
        payload: Mapping[str, object],
        *,
        context: LearnerRequestContext | None,
    ) -> AssessmentApiResponse:
        """Handle the future submit-attempt endpoint."""

        return self._run(
            payload=payload,
            context=context,
            operation=self._facade.submit,
            success_status=200,
        )

    def summary(
        self,
        payload: Mapping[str, object],
        *,
        context: LearnerRequestContext | None,
    ) -> AssessmentApiResponse:
        """Handle the framework-neutral subject-summary operation."""

        return self._run(
            payload=payload,
            context=context,
            operation=self._facade.summary,
            success_status=200,
        )

    def _run(
        self,
        *,
        payload: Mapping[str, object],
        context: LearnerRequestContext | None,
        operation: Callable[[Mapping[str, object]], dict[str, Any]],
        success_status: int,
    ) -> AssessmentApiResponse:
        authorization_error = self._authorize(payload=payload, context=context)
        if authorization_error is not None:
            return authorization_error

        try:
            return AssessmentApiResponse(
                status_code=success_status,
                body=operation(payload),
            )
        except AssessmentContractError as exc:
            return self._error_response(
                status_code=400,
                code="invalid_assessment_contract",
                message=str(exc),
            )
        except AssessmentGradingError:
            return self._error_response(
                status_code=503,
                code="assessment_grading_unavailable",
                message="The assessment could not be graded right now.",
            )
        except AssessmentFacadeError:
            return self._error_response(
                status_code=500,
                code="assessment_response_unavailable",
                message="The assessment response could not be built.",
            )
        except ValueError as exc:
            return self._error_response(
                status_code=422,
                code="assessment_request_rejected",
                message=str(exc),
            )

    @staticmethod
    def _authorize(
        *,
        payload: Mapping[str, object],
        context: LearnerRequestContext | None,
    ) -> AssessmentApiResponse | None:
        if context is None:
            return AssessmentApi._error_response(
                status_code=401,
                code="authentication_required",
                message="Learner authentication is required.",
            )
        if context.role != "learner":
            return AssessmentApi._error_response(
                status_code=403,
                code="learner_role_required",
                message="A learner role is required for assessment actions.",
            )
        requested_learner = payload.get("learner_id") if isinstance(payload, Mapping) else None
        if isinstance(requested_learner, str) and requested_learner != context.principal_id:
            return AssessmentApi._error_response(
                status_code=403,
                code="learner_context_mismatch",
                message="The request learner does not match the authenticated learner.",
            )
        return None

    @staticmethod
    def _error_response(
        *,
        status_code: int,
        code: str,
        message: str,
    ) -> AssessmentApiResponse:
        return AssessmentApiResponse(
            status_code=status_code,
            body={"error": {"code": code, "message": message}},
        )
