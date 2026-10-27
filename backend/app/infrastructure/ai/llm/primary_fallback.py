"""Validated primary-to-fallback routing for cloud generation providers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Protocol

from ....application.ports.ai import (
    AIIntegrationError,
    GeneratedContentValidatorPort,
    QuizDraft,
    QuizGenerationPort,
    QuizRequest,
    RetrievedSource,
    TutorDraft,
    TutorGenerationPort,
    TutorRequest,
)


class LearningGenerationProvider(TutorGenerationPort, QuizGenerationPort, Protocol):
    """Provider implementing both generation contracts."""


class PrimaryFallbackGenerator(TutorGenerationPort, QuizGenerationPort):
    """Try the primary provider, then fallback if generation or validation fails."""

    def __init__(
        self,
        *,
        primary: LearningGenerationProvider,
        fallback: LearningGenerationProvider,
        validator: GeneratedContentValidatorPort,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._validator = validator

    def generate(
        self,
        *,
        request: TutorRequest | QuizRequest,
        sources: Sequence[RetrievedSource],
    ) -> TutorDraft | QuizDraft:
        primary_error: Exception | None = None
        try:
            draft = self._primary.generate(request=request, sources=sources)
            self._validate(request=request, draft=draft, sources=sources)
            return draft
        except Exception as exc:
            primary_error = exc

        try:
            draft = self._fallback.generate(request=request, sources=sources)
            self._validate(request=request, draft=draft, sources=sources)
            return replace(draft, provider=f"fallback:{draft.provider}")
        except Exception as fallback_error:
            raise AIIntegrationError(
                "Primary generation and fallback generation both failed validation "
                f"({type(primary_error).__name__}, {type(fallback_error).__name__})"
            ) from fallback_error

    def _validate(
        self,
        *,
        request: TutorRequest | QuizRequest,
        draft: TutorDraft | QuizDraft,
        sources: Sequence[RetrievedSource],
    ) -> None:
        if isinstance(request, TutorRequest) and isinstance(draft, TutorDraft):
            self._validator.validate_tutor(request=request, draft=draft, sources=sources)
        elif isinstance(request, QuizRequest) and isinstance(draft, QuizDraft):
            self._validator.validate_quiz(request=request, draft=draft, sources=sources)
        else:
            raise AIIntegrationError("Provider returned a draft of the wrong type")
