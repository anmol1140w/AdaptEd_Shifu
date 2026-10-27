"""Mapping and validation for the teacher-intervention queue contract v1."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..application.use_cases.build_intervention_queue import (
    BuildInterventionQueueCommand,
    InterventionQueue,
    TeacherIntervention,
)


CONTRACT_VERSION = "v1"


class TeacherInterventionContractError(ValueError):
    """Raised when a teacher queue payload cannot cross the boundary."""


def parse_intervention_queue_request(
    payload: Mapping[str, object],
) -> BuildInterventionQueueCommand:
    """Validate and map a teacher queue request."""

    _require_exact_keys(
        payload,
        {"contract_version", "subject_id"},
        optional={"learner_ids"},
    )
    _require_version(payload)
    learner_ids_value = payload.get("learner_ids")
    learner_ids: tuple[str, ...] | None = None
    if learner_ids_value is not None:
        if not isinstance(learner_ids_value, list):
            raise TeacherInterventionContractError("learner_ids must be an array or null")
        normalized: list[str] = []
        for learner_id in learner_ids_value:
            if not isinstance(learner_id, str) or not learner_id.strip():
                raise TeacherInterventionContractError(
                    "learner_ids must contain non-empty strings"
                )
            normalized.append(learner_id)
        learner_ids = tuple(normalized)
    try:
        return BuildInterventionQueueCommand(
            subject_id=_required_string(payload, "subject_id"),
            learner_ids=learner_ids,
        )
    except ValueError as exc:
        raise TeacherInterventionContractError(str(exc)) from exc


def intervention_queue_response(
    result: InterventionQueue,
    *,
    subject_name: str,
) -> dict[str, Any]:
    """Map a queue to a JSON-safe response with evidence drill-down."""

    if not isinstance(subject_name, str) or not subject_name.strip():
        raise TeacherInterventionContractError("subject_name must be a non-empty string")
    if result.interventions and any(
        item.subject_id != result.subject_id for item in result.interventions
    ):
        raise TeacherInterventionContractError("intervention subject does not match queue subject")
    return {
        "contract_version": CONTRACT_VERSION,
        "subject": {"id": result.subject_id, "name": subject_name},
        "interventions": [_intervention_payload(item) for item in result.interventions],
    }


def _intervention_payload(item: TeacherIntervention) -> dict[str, Any]:
    return {
        "id": item.id,
        "learner_id": item.learner_id,
        "subject_id": item.subject_id,
        "concept": {
            "id": item.concept.id,
            "subject_id": item.concept.subject_id,
            "name": item.concept.name,
            "prerequisite_ids": list(item.concept.prerequisite_ids),
        },
        "priority": item.priority.value,
        "gap_status": item.gap_status.value,
        "action_type": item.recommendation.action_type.value,
        "reason": item.recommendation.reason,
        "teacher_review_required": item.recommendation.teacher_review_required,
        "mastery": None if item.mastery_state is None else {
            "concept_id": item.mastery_state.concept_id,
            "score": item.mastery_state.score,
            "confidence": item.mastery_state.confidence,
            "evidence_count": item.mastery_state.evidence_count,
            "trend": item.mastery_state.trend.value,
            "likely_misconception": item.mastery_state.likely_misconception,
            "recent_correctness": item.mastery_state.recent_correctness,
            "independence_score": item.mastery_state.independence_score,
        },
        "evidence_reference_ids": list(item.recommendation.evidence_ids),
        "evidence_count": len(item.evidence),
        "repeated_error_count": item.repeated_error_count,
        "average_hint_count": item.average_hint_count,
        "evidence": [
            {
                "id": attempt.id,
                "item_id": attempt.item_id,
                "concept_id": attempt.concept_id,
                "is_correct": attempt.is_correct,
                "difficulty": attempt.difficulty.value,
                "hint_count": attempt.hint_count,
                "misconception": attempt.misconception,
            }
            for attempt in item.evidence
        ],
    }


def _require_exact_keys(
    payload: Mapping[str, object],
    required: set[str],
    *,
    optional: set[str] | None = None,
) -> None:
    if not isinstance(payload, Mapping):
        raise TeacherInterventionContractError("payload must be an object")
    expected = required | (optional or set())
    missing = required - set(payload)
    unexpected = set(payload) - expected
    if missing:
        raise TeacherInterventionContractError(
            f"payload is missing required fields: {', '.join(sorted(missing))}"
        )
    if unexpected:
        raise TeacherInterventionContractError(
            f"payload contains unexpected fields: {', '.join(sorted(unexpected))}"
        )


def _require_version(payload: Mapping[str, object]) -> None:
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise TeacherInterventionContractError("contract_version must be 'v1'")


def _required_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise TeacherInterventionContractError(f"{field_name} must be a non-empty string")
    return value
