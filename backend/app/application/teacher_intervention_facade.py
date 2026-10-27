"""Framework-independent orchestration for teacher intervention requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..schemas.teacher_intervention_v1 import (
    intervention_queue_response,
    parse_intervention_queue_request,
)
from .use_cases.build_intervention_queue import BuildInterventionQueue


class TeacherInterventionFacadeError(ValueError):
    """Raised when a queue result cannot be mapped safely."""


class TeacherInterventionFacade:
    """Coordinate queue parsing, application execution and contract mapping."""

    def __init__(
        self,
        *,
        build_intervention_queue: BuildInterventionQueue,
        subject_names: Mapping[str, str],
    ) -> None:
        self._build_intervention_queue = build_intervention_queue
        self._subject_names = dict(subject_names)

    def queue(self, payload: Mapping[str, object]) -> dict[str, Any]:
        command = parse_intervention_queue_request(payload)
        result = self._build_intervention_queue.execute(command)
        try:
            subject_name = self._subject_names[command.subject_id]
        except KeyError as exc:
            raise TeacherInterventionFacadeError(
                f"unknown subject name: {command.subject_id}"
            ) from exc
        return intervention_queue_response(result, subject_name=subject_name)
