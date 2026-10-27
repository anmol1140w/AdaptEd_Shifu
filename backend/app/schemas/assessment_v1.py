"""Mapping and validation for the shared assessment contract v1."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..application.use_cases.build_subject_summary import (
    BuildSubjectSummaryCommand,
    SubjectSummary,
)
from ..application.use_cases.prepare_attempt import PrepareAttemptCommand
from ..application.use_cases.start_assessment import (
    StartAssessmentCommand,
    StartAssessmentResult,
)
from ..application.use_cases.submit_attempt import SubmitAttemptResult
from ..domain.entities.learning import (
    AssessmentItem,
    AssessmentSession,
    AttemptEvidence,
    Concept,
    Difficulty,
    MasteryState,
    Recommendation,
)


CONTRACT_VERSION = "v1"


class AssessmentContractError(ValueError):
    """Raised when a v1 assessment payload cannot cross the application boundary."""


SubmitAttemptRequest = PrepareAttemptCommand


def parse_start_assessment_request(
    payload: Mapping[str, object],
) -> StartAssessmentCommand:
    """Validate a v1 start payload and map it to the application command."""

    _require_exact_keys(payload, {"contract_version", "learner_id", "subject_id"})
    _require_version(payload)
    return StartAssessmentCommand(
        learner_id=_required_string(payload, "learner_id"),
        subject_id=_required_string(payload, "subject_id"),
    )


def parse_subject_summary_request(
    payload: Mapping[str, object],
) -> BuildSubjectSummaryCommand:
    """Validate a v1 subject-summary request and map it to the use case."""

    _require_exact_keys(payload, {"contract_version", "learner_id", "subject_id"})
    _require_version(payload)
    return BuildSubjectSummaryCommand(
        learner_id=_required_string(payload, "learner_id"),
        subject_id=_required_string(payload, "subject_id"),
    )


def parse_submit_attempt_request(
    payload: Mapping[str, object],
) -> SubmitAttemptRequest:
    """Validate a v1 raw-answer payload without attempting to grade it."""

    _require_exact_keys(payload, {"contract_version", "session_id", "learner_id", "attempt"})
    _require_version(payload)
    attempt = _required_mapping(payload, "attempt")
    _require_exact_keys(
        attempt,
        {
            "id",
            "item_id",
            "concept_id",
            "answer",
            "hint_count",
        },
        optional={"response_ms", "confidence_signal"},
    )

    response_ms = attempt.get("response_ms")
    if response_ms is not None and (
        not _is_integer(response_ms) or response_ms < 0
    ):
        raise AssessmentContractError("attempt.response_ms must be a non-negative integer or null")

    hint_count = attempt.get("hint_count")
    if not _is_integer(hint_count) or hint_count < 0:
        raise AssessmentContractError("attempt.hint_count must be a non-negative integer")

    confidence_signal = attempt.get("confidence_signal")
    if confidence_signal is not None and (
        not _is_number(confidence_signal) or not 0.0 <= confidence_signal <= 1.0
    ):
        raise AssessmentContractError(
            "attempt.confidence_signal must be a number in [0, 1] or null"
        )

    return SubmitAttemptRequest(
        session_id=_required_string(payload, "session_id"),
        learner_id=_required_string(payload, "learner_id"),
        attempt_id=_required_string(attempt, "id"),
        item_id=_required_string(attempt, "item_id"),
        concept_id=_required_string(attempt, "concept_id"),
        answer=_required_string(attempt, "answer"),
        response_ms=response_ms,
        hint_count=hint_count,
        confidence_signal=confidence_signal,
    )


def to_attempt_evidence(
    request: SubmitAttemptRequest,
    *,
    is_correct: bool,
    difficulty: Difficulty | str,
    misconception: str | None = None,
) -> AttemptEvidence:
    """Build domain evidence after a separate boundary has graded the answer."""

    if not isinstance(is_correct, bool):
        raise AssessmentContractError("is_correct must be a boolean")
    if misconception is not None and not misconception.strip():
        raise AssessmentContractError("misconception must not be empty when provided")
    return AttemptEvidence(
        id=request.attempt_id,
        item_id=request.item_id,
        concept_id=request.concept_id,
        is_correct=is_correct,
        difficulty=difficulty,
        hint_count=request.hint_count,
        response_ms=request.response_ms,
        confidence_signal=request.confidence_signal,
        misconception=misconception,
    )


def start_assessment_response(
    result: StartAssessmentResult,
    *,
    subject_name: str,
) -> dict[str, Any]:
    """Map a start result to the JSON-compatible v1 response shape."""

    _require_subject_name(subject_name)
    _require_session_subject(result.session, result.initial_concept.subject_id)
    if result.session.current_concept_id != result.initial_concept.id:
        raise AssessmentContractError(
            "session current concept does not match initial response concept"
        )
    _require_item_context(result.initial_item, result.initial_concept)
    return {
        "contract_version": CONTRACT_VERSION,
        "subject": {
            "id": result.session.subject_id,
            "name": subject_name,
        },
        "session": _session_payload(result.session),
        "concept": _concept_payload(result.initial_concept),
        "item": _item_payload(result.initial_item),
    }


def subject_summary_response(
    result: SubjectSummary,
    *,
    subject_name: str,
) -> dict[str, Any]:
    """Map a subject summary to a JSON-safe v1 response shape."""

    _require_subject_name(subject_name)
    if result.subject_id != result.concepts[0].concept.subject_id:
        raise AssessmentContractError("summary concept subject does not match summary subject")
    return {
        "contract_version": CONTRACT_VERSION,
        "learner_id": result.learner_id,
        "subject": {
            "id": result.subject_id,
            "name": subject_name,
        },
        "summary": {
            "mastery_score": result.mastery_score,
            "confidence": result.confidence,
            "evidence_count": result.evidence_count,
            "concept_count": len(result.concepts),
            "assessed_concept_count": sum(
                1 for concept in result.concepts if concept.evidence
            ),
            "gap_status_counts": [
                {"status": status.value, "count": count}
                for status, count in result.gap_status_counts
            ],
        },
        "concepts": [
            {
                "concept": _concept_payload(concept_summary.concept),
                "mastery": (
                    None
                    if concept_summary.mastery_state is None
                    else _mastery_payload(concept_summary.mastery_state)
                ),
                "gap_status": concept_summary.gap_status.value,
                "recommendation": (
                    None
                    if concept_summary.recommendation is None
                    else _recommendation_payload(concept_summary.recommendation)
                ),
                "evidence": [
                    _evidence_payload(attempt) for attempt in concept_summary.evidence
                ],
            }
            for concept_summary in result.concepts
        ],
    }


def submit_attempt_response(
    result: SubmitAttemptResult,
    *,
    subject_name: str,
    concept: Concept,
    item: AssessmentItem,
    evidence_references: Iterable[AttemptEvidence],
) -> dict[str, Any]:
    """Map a submitted-attempt result and loaded catalog context to v1."""

    _require_subject_name(subject_name)
    _require_session_subject(result.session, concept.subject_id)
    _require_item_context(item, concept)
    if result.attempt.item_id != item.id:
        raise AssessmentContractError("response item does not match evaluated attempt")
    if result.attempt.concept_id != concept.id:
        raise AssessmentContractError("response concept does not match evaluated attempt")
    if result.outcome.mastery_state.concept_id != concept.id:
        raise AssessmentContractError("mastery concept does not match evaluated concept")

    references = tuple(evidence_references)
    if not references:
        raise AssessmentContractError("at least one evidence reference is required")
    reference_ids = tuple(reference.id for reference in references)
    if len(set(reference_ids)) != len(reference_ids):
        raise AssessmentContractError("evidence reference IDs must be unique")
    recommendation = result.outcome.recommendation
    missing_ids = set(recommendation.evidence_ids) - set(reference_ids)
    if missing_ids:
        missing = ", ".join(sorted(missing_ids))
        raise AssessmentContractError(
            f"recommendation evidence references are missing from payload: {missing}"
        )
    if recommendation.target_concept_id != result.session.current_concept_id:
        raise AssessmentContractError(
            "session current concept must match the recommendation target"
        )

    return {
        "contract_version": CONTRACT_VERSION,
        "learner_id": result.learner_id,
        "subject": {
            "id": result.session.subject_id,
            "name": subject_name,
        },
        "session": _session_payload(result.session),
        "concept": _concept_payload(concept),
        "item": _item_payload(item),
        "evidence": _evidence_payload(result.attempt),
        "mastery": _mastery_payload(result.outcome.mastery_state),
        "gap_status": result.outcome.gap_status.value,
        "recommendation": _recommendation_payload(recommendation),
        "evidence_references": [
            _evidence_reference_payload(reference) for reference in references
        ],
    }


def _session_payload(session: AssessmentSession) -> dict[str, Any]:
    return {
        "id": session.id,
        "learner_id": session.learner_id,
        "subject_id": session.subject_id,
        "current_concept_id": session.current_concept_id,
        "status": session.status.value,
    }


def _concept_payload(concept: Concept) -> dict[str, Any]:
    return {
        "id": concept.id,
        "subject_id": concept.subject_id,
        "name": concept.name,
        "prerequisite_ids": list(concept.prerequisite_ids),
        "mastery_threshold": concept.mastery_threshold,
    }


def _item_payload(item: AssessmentItem) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item.id,
        "subject_id": item.subject_id,
        "concept_id": item.concept_id,
        "difficulty": item.difficulty.value,
        "question": item.question,
    }
    if item.source_id is not None:
        payload["source_id"] = item.source_id
    return payload


def _evidence_payload(attempt: AttemptEvidence) -> dict[str, Any]:
    return {
        "id": attempt.id,
        "item_id": attempt.item_id,
        "concept_id": attempt.concept_id,
        "is_correct": attempt.is_correct,
        "difficulty": attempt.difficulty.value,
        "hint_count": attempt.hint_count,
        "response_ms": attempt.response_ms,
        "confidence_signal": attempt.confidence_signal,
        "misconception": attempt.misconception,
    }


def _mastery_payload(state: MasteryState) -> dict[str, Any]:
    return {
        "concept_id": state.concept_id,
        "score": state.score,
        "confidence": state.confidence,
        "evidence_count": state.evidence_count,
        "trend": state.trend.value,
        "likely_misconception": state.likely_misconception,
        "recent_correctness": state.recent_correctness,
        "independence_score": state.independence_score,
    }


def _recommendation_payload(recommendation: Recommendation) -> dict[str, Any]:
    return {
        "action_type": recommendation.action_type.value,
        "target_concept_id": recommendation.target_concept_id,
        "reason": recommendation.reason,
        "evidence_reference_ids": list(recommendation.evidence_ids),
        "teacher_review_required": recommendation.teacher_review_required,
    }


def _evidence_reference_payload(attempt: AttemptEvidence) -> dict[str, Any]:
    return {
        "id": attempt.id,
        "item_id": attempt.item_id,
        "concept_id": attempt.concept_id,
        "is_correct": attempt.is_correct,
        "difficulty": attempt.difficulty.value,
        "hint_count": attempt.hint_count,
        "misconception": attempt.misconception,
    }


def _require_exact_keys(
    payload: Mapping[str, object],
    required: set[str],
    *,
    optional: set[str] | None = None,
) -> None:
    if not isinstance(payload, Mapping):
        raise AssessmentContractError("payload must be an object")
    optional_keys = optional or set()
    expected = required | optional_keys
    missing = required - set(payload)
    unexpected = set(payload) - expected
    if missing:
        raise AssessmentContractError(
            f"payload is missing required fields: {', '.join(sorted(missing))}"
        )
    if unexpected:
        raise AssessmentContractError(
            f"payload contains unexpected fields: {', '.join(sorted(unexpected))}"
        )


def _require_version(payload: Mapping[str, object]) -> None:
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise AssessmentContractError("contract_version must be 'v1'")


def _required_mapping(payload: Mapping[str, object], field_name: str) -> Mapping[str, object]:
    value = payload.get(field_name)
    if not isinstance(value, Mapping):
        raise AssessmentContractError(f"{field_name} must be an object")
    return value


def _required_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise AssessmentContractError(f"{field_name} must be a non-empty string")
    return value


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_subject_name(subject_name: str) -> None:
    if not isinstance(subject_name, str) or not subject_name.strip():
        raise AssessmentContractError("subject_name must be a non-empty string")


def _require_session_subject(session: AssessmentSession, subject_id: str) -> None:
    if session.subject_id != subject_id:
        raise AssessmentContractError("session subject does not match response context")


def _require_item_context(item: AssessmentItem, concept: Concept) -> None:
    if item.subject_id != concept.subject_id:
        raise AssessmentContractError("item subject does not match concept subject")
    if item.concept_id != concept.id:
        raise AssessmentContractError("item concept does not match response concept")
