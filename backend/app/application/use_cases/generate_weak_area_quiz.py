"""Application flow for grounded weak-area quiz generation."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.learning import Concept, Difficulty
from ..learning_context import load_learner_concept_context
from ..ports.ai import (
    AIAuditEvent,
    AIAuditPort,
    AIIntegrationError,
    GeneratedContentValidatorPort,
    QuizDraft,
    QuizGenerationPort,
    QuizItemDraft,
    QuizRepresentation,
    QuizRequest,
    RetrievalPort,
    RetrievalRequest,
)
from ..ports.assessment import ConceptCatalogPort
from ..ports.learning import AttemptPort, MasteryStatePort


@dataclass(frozen=True, slots=True)
class GenerateWeakAreaQuizCommand:
    """Validated learner context for one weak-area quiz request."""

    learner_id: str
    subject_id: str
    concept_id: str
    difficulty: Difficulty
    item_count: int = 3
    misconception: str | None = None
    include_transfer: bool = True

    def __post_init__(self) -> None:
        for field_name in ("learner_id", "subject_id", "concept_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not isinstance(self.difficulty, Difficulty):
            object.__setattr__(self, "difficulty", Difficulty(self.difficulty))
        if not isinstance(self.item_count, int) or isinstance(self.item_count, bool):
            raise ValueError("quiz item count must be an integer")
        if not 1 <= self.item_count <= 5:
            raise ValueError("quiz item count must be in [1, 5]")
        if self.misconception is not None and not self.misconception.strip():
            raise ValueError("misconception must not be empty when provided")
        if not isinstance(self.include_transfer, bool):
            raise ValueError("include_transfer must be a boolean")


@dataclass(frozen=True, slots=True)
class WeakAreaQuizResult:
    """Generated quiz plus fallback and audit metadata."""

    learner_id: str
    subject_id: str
    concept_id: str
    concept: Concept
    draft: QuizDraft
    fallback_used: bool
    audit_event_id: str
    effective_difficulty: Difficulty = Difficulty.MEDIUM
    evidence_reference_ids: tuple[str, ...] = ()
    evidence_count: int = 0
    mastery_score: float | None = None
    mastery_confidence: float | None = None
    gap_status: str | None = None


class GenerateWeakAreaQuiz:
    """Coordinate retrieval, quiz generation, validation, fallback and audit."""

    _MIN_RETRIEVAL_CONFIDENCE = 0.6

    def __init__(
        self,
        *,
        concepts: ConceptCatalogPort,
        retriever: RetrievalPort,
        generator: QuizGenerationPort,
        fallback_generator: QuizGenerationPort,
        validator: GeneratedContentValidatorPort,
        audit: AIAuditPort,
        attempts: AttemptPort | None = None,
        mastery_states: MasteryStatePort | None = None,
    ) -> None:
        self._concepts = concepts
        self._retriever = retriever
        self._generator = generator
        self._fallback_generator = fallback_generator
        self._validator = validator
        self._audit = audit
        self._attempts = attempts
        self._mastery_states = mastery_states

    def execute(self, command: GenerateWeakAreaQuizCommand) -> WeakAreaQuizResult:
        """Return aligned quiz items or a safe teacher-review fallback."""

        concept = self._concept_for(command.subject_id, command.concept_id)
        context = load_learner_concept_context(
            learner_id=command.learner_id,
            concept=concept,
            concepts=self._concepts.list_concepts(command.subject_id),
            attempts=self._attempts,
            mastery_states=self._mastery_states,
        )
        effective_difficulty = self._effective_difficulty(command, context)
        misconception = context.misconception or command.misconception
        request = QuizRequest(
            learner_id=command.learner_id,
            subject_id=command.subject_id,
            concept_id=command.concept_id,
            difficulty=effective_difficulty,
            item_count=command.item_count,
            misconception=misconception,
            include_transfer=command.include_transfer,
            evidence_ids=context.evidence_ids,
            evidence_count=len(context.evidence),
            mastery_score=(None if context.mastery_state is None else context.mastery_state.score),
            mastery_confidence=(
                None
                if context.mastery_state is None
                else context.mastery_state.confidence
            ),
            gap_status=(None if context.gap_status is None else context.gap_status.value),
        )
        retrieval_request = RetrievalRequest(
            subject_id=command.subject_id,
            concept_id=command.concept_id,
            query=f"{concept.name} {misconception or ''}".strip(),
            misconception=misconception,
        )

        fallback_used = False
        validation_flags: list[str] = []
        retrieval = None
        try:
            retrieval = self._retriever.retrieve(retrieval_request)
            has_usable_retrieval = bool(
                retrieval.sources
                and retrieval.confidence >= self._MIN_RETRIEVAL_CONFIDENCE
            )
        except Exception:
            has_usable_retrieval = False
            fallback_used = True
            validation_flags.append("retrieval_failed")

        if not has_usable_retrieval:
            fallback_used = True
            validation_flags.append(
                "no_approved_source"
                if retrieval is None or not getattr(retrieval, "sources", ())
                else "low_confidence_retrieval"
            )
            draft = self._safe_fallback(
                request=request,
                validation_flags=validation_flags,
            )
        else:
            try:
                draft = self._generator.generate(
                    request=request,
                    sources=retrieval.sources,
                )
                self._validator.validate_quiz(
                    request=request,
                    draft=draft,
                    sources=retrieval.sources,
                )
            except Exception:
                fallback_used = True
                validation_flags.append("generated_output_failed")
                draft = self._safe_fallback(
                    request=request,
                    validation_flags=validation_flags,
                )

        try:
            audit_event_id = self._audit.record(
                AIAuditEvent(
                    event_type="weak_area_quiz",
                    learner_id=command.learner_id,
                    subject_id=command.subject_id,
                    concept_id=command.concept_id,
                    provider=draft.provider,
                    fallback_used=fallback_used,
                    source_ids=draft.source_ids,
                    validation_flags=tuple(validation_flags),
                )
            )
        except Exception:
            audit_event_id = "audit-unavailable"
        return WeakAreaQuizResult(
            learner_id=command.learner_id,
            subject_id=command.subject_id,
            concept_id=command.concept_id,
            concept=concept,
            draft=draft,
            fallback_used=fallback_used,
            audit_event_id=audit_event_id,
            effective_difficulty=effective_difficulty,
            evidence_reference_ids=context.evidence_ids,
            evidence_count=len(context.evidence),
            mastery_score=(None if context.mastery_state is None else context.mastery_state.score),
            mastery_confidence=(
                None
                if context.mastery_state is None
                else context.mastery_state.confidence
            ),
            gap_status=(None if context.gap_status is None else context.gap_status.value),
        )

    @staticmethod
    def _effective_difficulty(command: GenerateWeakAreaQuizCommand, context) -> Difficulty:
        """Scaffold weak evidence and raise secure transfer practice."""

        if context.gap_status is not None and context.gap_status.value in {
            "prerequisite_blocked",
            "needs_support",
        }:
            return Difficulty.EASY
        if (
            context.recommendation is not None
            and context.recommendation.action_type.value == "transfer_practice"
            and command.include_transfer
        ):
            return Difficulty.HARD
        return command.difficulty

    def _safe_fallback(
        self,
        *,
        request: QuizRequest,
        validation_flags: list[str],
    ) -> QuizDraft:
        try:
            draft = self._fallback_generator.generate(request=request, sources=())
            self._validator.validate_quiz(request=request, draft=draft, sources=())
            return draft
        except Exception:
            validation_flags.append("fallback_failed")
            items = tuple(
                QuizItemDraft(
                    id=f"emergency-quiz-{request.concept_id.lower()}-{index}",
                    subject_id=request.subject_id,
                    concept_id=request.concept_id,
                    difficulty=request.difficulty,
                    question=(
                        "Transfer check: identify the first operation needed for this concept step."
                        if request.include_transfer and index == request.item_count
                        else "Identify the first operation needed for this concept step."
                    ),
                    answer="identify the first operation",
                    representation=QuizRepresentation.VERBAL,
                    source_ids=(),
                    is_transfer=request.include_transfer and index == request.item_count,
                )
                for index in range(1, request.item_count + 1)
            )
            return QuizDraft(
                items=items,
                source_ids=(),
                confidence=0.1,
                teacher_review_required=True,
                provider="emergency-fallback",
            )

    def _concept_for(self, subject_id: str, concept_id: str) -> Concept:
        concept = next(
            (
                candidate
                for candidate in self._concepts.list_concepts(subject_id)
                if candidate.id == concept_id
            ),
            None,
        )
        if concept is None:
            raise ValueError(f"unknown concept for subject: {concept_id}")
        return concept
