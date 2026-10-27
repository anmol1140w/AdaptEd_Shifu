"""Application flow for grounded tutor hints and explanations."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.learning import Concept
from ..ports.ai import (
    AIAuditEvent,
    AIAuditPort,
    AIIntegrationError,
    GeneratedContentValidatorPort,
    RetrievalPort,
    RetrievalRequest,
    TutorDraft,
    TutorGenerationPort,
    TutorMode,
    TutorRequest,
)
from ..ports.assessment import ConceptCatalogPort


@dataclass(frozen=True, slots=True)
class ProvideTutorSupportCommand:
    """Validated learner context for one tutor-support request."""

    learner_id: str
    subject_id: str
    concept_id: str
    mode: TutorMode
    learner_answer: str | None = None
    misconception: str | None = None
    learner_level: str = "class_9"

    def __post_init__(self) -> None:
        for field_name in ("learner_id", "subject_id", "concept_id", "learner_level"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not isinstance(self.mode, TutorMode):
            object.__setattr__(self, "mode", TutorMode(self.mode))
        if self.learner_answer is not None and not self.learner_answer.strip():
            raise ValueError("learner answer must not be empty when provided")
        if self.misconception is not None and not self.misconception.strip():
            raise ValueError("misconception must not be empty when provided")


@dataclass(frozen=True, slots=True)
class TutorSupportResult:
    """Tutor output plus fallback and audit metadata."""

    learner_id: str
    subject_id: str
    concept_id: str
    concept: Concept
    draft: TutorDraft
    fallback_used: bool
    audit_event_id: str


class ProvideTutorSupport:
    """Coordinate retrieval, generation, validation, fallback and audit."""

    _MIN_RETRIEVAL_CONFIDENCE = 0.6

    def __init__(
        self,
        *,
        concepts: ConceptCatalogPort,
        retriever: RetrievalPort,
        generator: TutorGenerationPort,
        fallback_generator: TutorGenerationPort,
        validator: GeneratedContentValidatorPort,
        audit: AIAuditPort,
    ) -> None:
        self._concepts = concepts
        self._retriever = retriever
        self._generator = generator
        self._fallback_generator = fallback_generator
        self._validator = validator
        self._audit = audit

    def execute(self, command: ProvideTutorSupportCommand) -> TutorSupportResult:
        """Return grounded tutor support or a safe curated fallback."""

        concept = self._concept_for(command.subject_id, command.concept_id)
        request = TutorRequest(
            learner_id=command.learner_id,
            subject_id=command.subject_id,
            concept_id=command.concept_id,
            mode=command.mode,
            learner_answer=command.learner_answer,
            misconception=command.misconception,
            learner_level=command.learner_level,
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
            self._validator.validate_tutor(request=request, draft=draft, sources=())
        else:
            try:
                draft = self._generator.generate(
                    request=request,
                    sources=retrieval.sources,
                )
                self._validator.validate_tutor(
                    request=request,
                    draft=draft,
                    sources=retrieval.sources,
                )
            except (AIIntegrationError, ValueError):
                fallback_used = True
                validation_flags.append("generated_output_failed")
                draft = self._fallback_generator.generate(request=request, sources=())
                self._validator.validate_tutor(request=request, draft=draft, sources=())

        audit_event_id = self._audit.record(
            AIAuditEvent(
                event_type="tutor_response",
                learner_id=command.learner_id,
                subject_id=command.subject_id,
                concept_id=command.concept_id,
                provider=draft.provider,
                fallback_used=fallback_used,
                source_ids=draft.source_ids,
                validation_flags=tuple(validation_flags),
            )
        )
        return TutorSupportResult(
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
