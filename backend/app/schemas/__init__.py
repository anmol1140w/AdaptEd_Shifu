"""Validated backend boundary shapes aligned with shared contracts."""

from .assessment_v1 import (
    AssessmentContractError,
    SubmitAttemptRequest,
    parse_start_assessment_request,
    parse_submit_attempt_request,
    start_assessment_response,
    submit_attempt_response,
    to_attempt_evidence,
)
from .learning_support_v1 import (
    LearningSupportContractError,
    parse_tutor_request,
    parse_weak_area_quiz_request,
    tutor_response,
    weak_area_quiz_response,
)

__all__ = [
    "AssessmentContractError",
    "SubmitAttemptRequest",
    "parse_start_assessment_request",
    "parse_submit_attempt_request",
    "start_assessment_response",
    "submit_attempt_response",
    "to_attempt_evidence",
    "LearningSupportContractError",
    "parse_tutor_request",
    "parse_weak_area_quiz_request",
    "tutor_response",
    "weak_area_quiz_response",
]
