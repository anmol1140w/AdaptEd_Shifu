"""Deterministic tutor and quiz adapters for local execution and tests."""

from __future__ import annotations

from collections.abc import Sequence

from ....application.ports.ai import (
    QuizDraft,
    QuizGenerationPort,
    QuizItemDraft,
    QuizRepresentation,
    QuizRequest,
    RetrievedSource,
    TutorDraft,
    TutorGenerationPort,
    TutorMode,
    TutorRequest,
)


class DeterministicTutorGenerator(TutorGenerationPort):
    """Produce inspectable hint-first responses without network access."""

    def generate(
        self,
        *,
        request: TutorRequest,
        sources: Sequence[RetrievedSource],
    ) -> TutorDraft:
        source_ids = tuple(source.source_id for source in sources[:1])
        misconception = (request.misconception or "").lower()
        if "negative sign" in misconception or "distribut" in misconception:
            message = "The negative multiplier applies to every term inside the bracket."
            check_question = "Which term has not received the multiplier yet?"
        elif request.mode is TutorMode.EXPLANATION:
            message = (
                "Apply the outside factor to every term inside the brackets, "
                "then combine like terms."
            )
            check_question = "Can you apply the multiplier to both terms?"
        elif request.mode is TutorMode.CHECK_QUESTION:
            message = "Try the next step before checking the worked example."
            check_question = "What operation should happen first?"
        else:
            message = "Look at every term inside the brackets before simplifying."
            check_question = "Which term needs the same operation as the first term?"

        return TutorDraft(
            mode=request.mode,
            message=message,
            check_question=check_question,
            source_ids=source_ids,
            confidence=max((source.confidence for source in sources[:1]), default=0.85),
            teacher_review_required=False,
            answer_revealed=False,
            provider="mock-deterministic",
        )


class CuratedTutorFallback(TutorGenerationPort):
    """Return a safe non-spoiler response when retrieval or generation is unavailable."""

    def generate(
        self,
        *,
        request: TutorRequest,
        sources: Sequence[RetrievedSource],
    ) -> TutorDraft:
        del sources
        return TutorDraft(
            mode=request.mode,
            message=(
                "Start by identifying the operation applied to the first term. "
                "A teacher-reviewed example is needed before giving more detail."
            ),
            check_question="What operation will you apply to the next term?",
            source_ids=(),
            confidence=0.2,
            teacher_review_required=True,
            answer_revealed=False,
            provider="curated-fallback",
        )


class DeterministicQuizGenerator(QuizGenerationPort):
    """Produce structured weak-area practice items with stable local answers."""

    def generate(
        self,
        *,
        request: QuizRequest,
        sources: Sequence[RetrievedSource],
    ) -> QuizDraft:
        source_ids = tuple(source.source_id for source in sources[:1])
        items = tuple(
            self._item(request=request, index=index, source_ids=source_ids)
            for index in range(1, request.item_count + 1)
        )
        return QuizDraft(
            items=items,
            source_ids=source_ids,
            confidence=max((source.confidence for source in sources[:1]), default=0.85),
            teacher_review_required=False,
            provider="mock-deterministic",
        )

    @staticmethod
    def _item(
        *,
        request: QuizRequest,
        index: int,
        source_ids: tuple[str, ...],
    ) -> QuizItemDraft:
        is_transfer = request.include_transfer and index == request.item_count
        concept_label = request.concept_id.replace("-", " ").title()
        if "DIST" in request.concept_id:
            templates = (
                ("Expand -2(x + 3).", "-2x - 6", QuizRepresentation.SYMBOLIC),
                (
                    "A negative factor multiplies (y + 4). Which operation applies to y?",
                    "multiply y by the negative factor",
                    QuizRepresentation.VERBAL,
                ),
                (
                    "A rectangle has side length (n + 2) and width 3. Write its area.",
                    "3n + 6",
                    QuizRepresentation.STORY,
                ),
            )
        else:
            templates = (
                ("Solve x + 3 = 7.", "x = 4", QuizRepresentation.SYMBOLIC),
                ("Solve 2x + 5 = 15.", "x = 5", QuizRepresentation.SYMBOLIC),
                (
                    "A number doubled and increased by 5 is 15. What is the number?",
                    "5",
                    QuizRepresentation.STORY,
                ),
            )
        question, answer, representation = templates[(index - 1) % len(templates)]
        if is_transfer:
            question = f"Transfer check for {concept_label}: {question}"
        return QuizItemDraft(
            id=f"mock-quiz-{request.concept_id.lower()}-{index}",
            subject_id=request.subject_id,
            concept_id=request.concept_id,
            difficulty=request.difficulty,
            question=question,
            answer=answer,
            representation=representation,
            source_ids=source_ids,
            is_transfer=is_transfer,
        )


class CuratedQuizFallback(QuizGenerationPort):
    """Return safe structured practice when retrieval or generation is unavailable."""

    def generate(
        self,
        *,
        request: QuizRequest,
        sources: Sequence[RetrievedSource],
    ) -> QuizDraft:
        del sources
        items = tuple(
            QuizItemDraft(
                id=f"fallback-quiz-{request.concept_id.lower()}-{index}",
                subject_id=request.subject_id,
                concept_id=request.concept_id,
                difficulty=request.difficulty,
                question="Identify the first operation needed to solve this concept step.",
                answer="identify the first operation",
                representation=QuizRepresentation.VERBAL,
                source_ids=(),
                is_transfer=False,
            )
            for index in range(1, request.item_count + 1)
        )
        return QuizDraft(
            items=items,
            source_ids=(),
            confidence=0.2,
            teacher_review_required=True,
            provider="curated-fallback",
        )
