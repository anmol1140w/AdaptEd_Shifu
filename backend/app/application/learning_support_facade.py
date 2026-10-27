"""Framework-independent orchestration for tutor and weak-area quiz flows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..schemas.learning_support_v1 import (
    parse_tutor_request,
    parse_weak_area_quiz_request,
    tutor_response,
    weak_area_quiz_response,
)
from .use_cases.generate_weak_area_quiz import GenerateWeakAreaQuiz
from .use_cases.provide_tutor_support import ProvideTutorSupport


class LearningSupportFacadeError(ValueError):
    """Raised when support output cannot be mapped safely."""


class LearningSupportFacade:
    """Coordinate support request parsing, use cases and contract mapping."""

    def __init__(
        self,
        *,
        provide_tutor_support: ProvideTutorSupport,
        generate_weak_area_quiz: GenerateWeakAreaQuiz,
    ) -> None:
        self._provide_tutor_support = provide_tutor_support
        self._generate_weak_area_quiz = generate_weak_area_quiz

    def tutor(self, payload: Mapping[str, object]) -> dict[str, Any]:
        """Run the grounded tutor flow and return a v1 response."""

        command = parse_tutor_request(payload)
        result = self._provide_tutor_support.execute(command)
        return tutor_response(result)

    def weak_area_quiz(self, payload: Mapping[str, object]) -> dict[str, Any]:
        """Run weak-area quiz generation and return a v1 response."""

        command = parse_weak_area_quiz_request(payload)
        result = self._generate_weak_area_quiz.execute(command)
        return weak_area_quiz_response(result)
