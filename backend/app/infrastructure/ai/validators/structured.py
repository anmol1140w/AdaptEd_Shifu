"""Dependency-free validation for tutor and quiz generated output."""

from __future__ import annotations

from collections.abc import Sequence

from ....application.ports.ai import (
    AIValidationError,
    GeneratedContentValidatorPort,
    QuizDraft,
    QuizRequest,
    RetrievedSource,
    TutorDraft,
    TutorMode,
    TutorRequest,
)


class StructuredLearningOutputValidator(GeneratedContentValidatorPort):
    """Reject unsupported sources, concept drift and spoiler hints."""

    def validate_tutor(
        self,
        *,
        request: TutorRequest,
        draft: TutorDraft,
        sources: Sequence[RetrievedSource],
    ) -> None:
        if draft.mode is not request.mode:
            raise AIValidationError("tutor mode does not match request")
        self._validate_source_ids(
            draft.source_ids,
            sources,
            subject_id=request.subject_id,
            concept_id=request.concept_id,
        )
        if request.mode is TutorMode.HINT and draft.answer_revealed:
            raise AIValidationError("hint response must not reveal the answer")
        if not draft.check_question.strip():
            raise AIValidationError("tutor response must include a check question")

    def validate_quiz(
        self,
        *,
        request: QuizRequest,
        draft: QuizDraft,
        sources: Sequence[RetrievedSource],
    ) -> None:
        if len(draft.items) != request.item_count:
            raise AIValidationError("quiz item count does not match request")
        self._validate_source_ids(
            draft.source_ids,
            sources,
            subject_id=request.subject_id,
            concept_id=request.concept_id,
        )
        draft_source_ids = set(draft.source_ids)
        for item in draft.items:
            if item.subject_id != request.subject_id:
                raise AIValidationError("quiz item subject does not match request")
            if item.concept_id != request.concept_id:
                raise AIValidationError("quiz item concept does not match request")
            if item.difficulty is not request.difficulty:
                raise AIValidationError("quiz item difficulty does not match request")
            if not set(item.source_ids).issubset(draft_source_ids):
                raise AIValidationError("quiz item uses an undeclared source")

    @staticmethod
    def _validate_source_ids(
        source_ids: Sequence[str],
        sources: Sequence[RetrievedSource],
        *,
        subject_id: str,
        concept_id: str,
    ) -> None:
        source_map = {source.source_id: source for source in sources}
        for source_id in source_ids:
            source = source_map.get(source_id)
            if source is None:
                raise AIValidationError(f"generated content references unsupported source: {source_id}")
            if not source.approved:
                raise AIValidationError(f"generated content references unapproved source: {source_id}")
            if source.subject_id != subject_id or source.concept_id != concept_id:
                raise AIValidationError(f"generated content source is outside the requested concept: {source_id}")
