"""Thin v1 route adapter for teacher intervention queue requests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ....application.teacher_intervention_facade import (
    TeacherInterventionFacade,
    TeacherInterventionFacadeError,
)
from ....schemas.teacher_intervention_v1 import TeacherInterventionContractError
from .assessment import AssessmentApiResponse


@dataclass(frozen=True, slots=True)
class TeacherRequestContext:
    """Trusted teacher identity and authorized learner-group boundary."""

    principal_id: str
    role: str = "teacher"
    allowed_learner_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.principal_id.strip():
            raise ValueError("request principal id must not be empty")
        if not self.role.strip():
            raise ValueError("request role must not be empty")
        learner_ids = tuple(self.allowed_learner_ids)
        if any(not learner_id.strip() for learner_id in learner_ids):
            raise ValueError("authorized learner IDs must not be empty")
        if len(set(learner_ids)) != len(learner_ids):
            raise ValueError("authorized learner IDs must be unique")
        object.__setattr__(self, "allowed_learner_ids", learner_ids)


@dataclass(frozen=True, slots=True)
class TeacherInterventionApi:
    """Adapt trusted teacher context to the queue facade."""

    facade: TeacherInterventionFacade

    QUEUE_PATH = "/api/v1/teacher/interventions"

    def queue(
        self,
        payload: Mapping[str, object],
        *,
        context: TeacherRequestContext | None,
    ) -> AssessmentApiResponse:
        if context is None:
            return self._error(401, "authentication_required", "Teacher authentication is required.")
        if context.role != "teacher":
            return self._error(403, "teacher_role_required", "A teacher role is required for intervention actions.")
        requested = payload.get("learner_ids") if isinstance(payload, Mapping) else None
        if requested is not None and not isinstance(requested, list):
            return self._error(400, "invalid_teacher_intervention_contract", "learner_ids must be an array or null")
        if context.allowed_learner_ids and requested is not None:
            requested_ids = {value for value in requested if isinstance(value, str)}
            if not requested_ids.issubset(set(context.allowed_learner_ids)):
                return self._error(403, "learner_group_forbidden", "The teacher is not authorized for every requested learner.")
        authorized_payload = dict(payload)
        if context.allowed_learner_ids and requested is None:
            authorized_payload["learner_ids"] = list(context.allowed_learner_ids)
        try:
            return AssessmentApiResponse(status_code=200, body=self.facade.queue(authorized_payload))
        except TeacherInterventionContractError as exc:
            return self._error(400, "invalid_teacher_intervention_contract", str(exc))
        except TeacherInterventionFacadeError:
            return self._error(500, "teacher_intervention_response_unavailable", "The intervention queue could not be built.")
        except ValueError as exc:
            return self._error(422, "teacher_intervention_request_rejected", str(exc))

    @staticmethod
    def _error(status_code: int, code: str, message: str) -> AssessmentApiResponse:
        return AssessmentApiResponse(
            status_code=status_code,
            body={"error": {"code": code, "message": message}},
        )
