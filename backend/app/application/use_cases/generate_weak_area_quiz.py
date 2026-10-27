"""Application flow for grounded weak-area quiz generation."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.learning import Concept, Difficulty
from ..ports.ai import (
    AIAuditEvent,
    AIAuditPort,
    AIIntegrationError,
    GeneratedContentValidatorPort,
    QuizDraft,
    QuizGenerationPort,
    QuizRequest,
    RetrievalPort,
    RetrievalRequest,
)
from ..ports.assessment import ConceptCatalogPort


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
    ) -> None:
        self._concepts = concepts
        self._retriever = retriever
        self._generator = generator
        self._fallback_generator = fallback_generator
        self._validator = validator
        self._audit = audit

    def execute(self, command: GenerateWeakAreaQuizCommand) -> WeakAreaQuizResult:
        """Return aligned quiz items or a safe teacher-review fallback."""

        concept = self._concept_for(command.subject_id, command.concept_id)
        request = QuizRequest(
            learner_id=command.learner_id,
            subject_id=command.subject_id,
            concept_id=command.concept_id,
            difficulty=command.difficulty,
            item_count=command.item_count,
            misconception=command.misconception,
            include_transfer=command.include_transfer,
        )
        retrieval_request = RetrievalRequest(
            subject_id=command.subject_id,
            concept_id=command.concept_id,
            query=f"{concept.name} {command.misconception or ''}".strip(),
            misconception=command.misconception,
        )

        fallback_used = False
        validation_flags: list[str] = []
        try:
            retrieval = self._retriever.retrieve(retrieval_request)
        except (AIIntegrationError, ValueError):
            retrieval = None
            fallback_used = True
            validation_flags.append("retrieval_failed")

        if retrieval is None or not retrieval.sources or retrieval.confidence < self._MIN_RETRIEVAL_CONFIDENCE:
            fallback_used = True
            validation_flags.append(
                "no_approved_source" if retrieval is None or not retrieval.sources else "low_confidence_retrieval"
            )
            draft = self._fallback_generator.generate(request=request, sources=())
            self._validator.validate_quiz(request=request, draft=draft, sources=())
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
            except (AIIntegrationError, ValueError):
                fallback_used = True
                validation_flags.append("generated_output_failed")
                draft = self._fallback_generator.generate(request=request, sources=())
                self._validator.validate_quiz(request=request, draft=draft, sources=())

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
        return WeakAreaQuizResult(
            learner_id=command.learner_id,
            subject_id=command.subject_id,
            concept_id=command.concept_id,
            concept=concept,
            draft=draft,
            fallback_used=fallback_used,
            audit_event_id=audit_event_id,
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
