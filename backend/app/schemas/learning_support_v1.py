"""Mapping and validation for tutor and weak-area quiz contracts v1."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..application.use_cases.generate_weak_area_quiz import (
    GenerateWeakAreaQuizCommand,
    WeakAreaQuizResult,
)
from ..application.use_cases.provide_tutor_support import (
    ProvideTutorSupportCommand,
    TutorSupportResult,
)
from ..domain.entities.learning import Difficulty
from ..application.ports.ai import TutorMode


CONTRACT_VERSION = "v1"


class LearningSupportContractError(ValueError):
    """Raised when tutor or quiz payloads cannot cross the application boundary."""


def parse_tutor_request(
    payload: Mapping[str, object],
) -> ProvideTutorSupportCommand:
    """Validate and map a tutor-support request."""

    _require_exact_keys(
        payload,
        {"contract_version", "learner_id", "subject_id", "concept_id", "mode"},
        optional={"learner_answer", "misconception", "learner_level"},
    )
    _require_version(payload)
    mode_value = _required_string(payload, "mode")
    try:
        mode = TutorMode(mode_value)
    except ValueError as exc:
        raise LearningSupportContractError(
            "mode must be one of: hint, explanation, check_question"
        ) from exc
    return ProvideTutorSupportCommand(
        learner_id=_required_string(payload, "learner_id"),
        subject_id=_required_string(payload, "subject_id"),
        concept_id=_required_string(payload, "concept_id"),
        mode=mode,
        learner_answer=_optional_string(payload, "learner_answer"),
        misconception=_optional_string(payload, "misconception"),
        learner_level=_optional_string(payload, "learner_level") or "class_9",
    )


def parse_weak_area_quiz_request(
    payload: Mapping[str, object],
) -> GenerateWeakAreaQuizCommand:
    """Validate and map a weak-area quiz request."""

    _require_exact_keys(
        payload,
        {"contract_version", "learner_id", "subject_id", "concept_id", "difficulty"},
        optional={"item_count", "misconception", "include_transfer"},
    )
    _require_version(payload)
    difficulty_value = _required_string(payload, "difficulty")
    try:
        difficulty = Difficulty(difficulty_value)
    except ValueError as exc:
        raise LearningSupportContractError(
            "difficulty must be one of: easy, medium, hard"
        ) from exc

    item_count = payload.get("item_count", 3)
    if not _is_integer(item_count) or not 1 <= item_count <= 5:
        raise LearningSupportContractError("item_count must be an integer in [1, 5]")
    include_transfer = payload.get("include_transfer", True)
    if not isinstance(include_transfer, bool):
        raise LearningSupportContractError("include_transfer must be a boolean")

    return GenerateWeakAreaQuizCommand(
        learner_id=_required_string(payload, "learner_id"),
        subject_id=_required_string(payload, "subject_id"),
        concept_id=_required_string(payload, "concept_id"),
        difficulty=difficulty,
        item_count=item_count,
        misconception=_optional_string(payload, "misconception"),
        include_transfer=include_transfer,
    )


def tutor_response(result: TutorSupportResult) -> dict[str, Any]:
    """Map tutor output without exposing unsupported answer content."""

    draft = result.draft
    return {
        "contract_version": CONTRACT_VERSION,
        "learner_id": result.learner_id,
        "subject_id": result.subject_id,
        "concept_id": result.concept_id,
        "mode": draft.mode.value,
        "message": draft.message,
        "check_question": draft.check_question,
        "source_ids": list(draft.source_ids),
        "confidence": draft.confidence,
        "teacher_review_required": draft.teacher_review_required,
        "answer_revealed": draft.answer_revealed,
        "fallback_used": result.fallback_used,
        "provider": draft.provider,
        "audit_event_id": result.audit_event_id,
    }


def weak_area_quiz_response(result: WeakAreaQuizResult) -> dict[str, Any]:
    """Map generated quiz items while redacting their expected answers."""

    draft = result.draft
    return {
        "contract_version": CONTRACT_VERSION,
        "learner_id": result.learner_id,
        "subject_id": result.subject_id,
        "concept": {
            "id": result.concept.id,
            "subject_id": result.concept.subject_id,
            "name": result.concept.name,
            "prerequisite_ids": list(result.concept.prerequisite_ids),
        },
        "difficulty": draft.items[0].difficulty.value,
        "items": [
            {
                "id": item.id,
                "subject_id": item.subject_id,
                "concept_id": item.concept_id,
                "difficulty": item.difficulty.value,
                "question": item.question,
                "representation": item.representation.value,
                "source_ids": list(item.source_ids),
                "is_transfer": item.is_transfer,
            }
            for item in draft.items
        ],
        "source_ids": list(draft.source_ids),
        "confidence": draft.confidence,
        "teacher_review_required": draft.teacher_review_required,
        "fallback_used": result.fallback_used,
        "provider": draft.provider,
        "audit_event_id": result.audit_event_id,
    }


def _require_exact_keys(
    payload: Mapping[str, object],
    required: set[str],
    *,
    optional: set[str] | None = None,
) -> None:
    if not isinstance(payload, Mapping):
        raise LearningSupportContractError("payload must be an object")
    expected = required | (optional or set())
    missing = required - set(payload)
    unexpected = set(payload) - expected
    if missing:
        raise LearningSupportContractError(
            f"payload is missing required fields: {', '.join(sorted(missing))}"
        )
    if unexpected:
        raise LearningSupportContractError(
            f"payload contains unexpected fields: {', '.join(sorted(unexpected))}"
        )


def _require_version(payload: Mapping[str, object]) -> None:
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise LearningSupportContractError("contract_version must be 'v1'")


def _required_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise LearningSupportContractError(f"{field_name} must be a non-empty string")
    return value


def _optional_string(payload: Mapping[str, object], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise LearningSupportContractError(f"{field_name} must be a non-empty string or null")
    return value


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
