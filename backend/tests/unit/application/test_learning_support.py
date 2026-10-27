"""Behavior tests for tutor and weak-area quiz application flows."""

from __future__ import annotations

import unittest

from backend.app.application.ports.ai import (
    AIIntegrationError,
    RetrievedSource,
    TutorDraft,
    TutorGenerationPort,
    TutorMode,
    QuizGenerationPort,
)
from backend.app.application.use_cases.generate_weak_area_quiz import (
    GenerateWeakAreaQuiz,
    GenerateWeakAreaQuizCommand,
)
from backend.app.application.use_cases.provide_tutor_support import (
    ProvideTutorSupport,
    ProvideTutorSupportCommand,
)
from backend.app.domain.entities.learning import AttemptEvidence, Concept, Difficulty
from backend.app.infrastructure.ai.audit import InMemoryAIAudit
from backend.app.infrastructure.ai.llm import (
    CuratedQuizFallback,
    CuratedTutorFallback,
    DeterministicQuizGenerator,
    DeterministicTutorGenerator,
)
from backend.app.infrastructure.ai.retrieval import InMemoryLearningRetriever
from backend.app.infrastructure.ai.validators import StructuredLearningOutputValidator
from backend.app.infrastructure.in_memory import (
    InMemoryAttempts,
    InMemoryConceptCatalog,
    InMemoryMasteryStates,
)


class CapturingTutorGenerator(TutorGenerationPort):
    def __init__(self) -> None:
        self.requests = []

    def generate(self, *, request, sources):
        self.requests.append(request)
        return TutorDraft(
            mode=request.mode,
            message="Use the same operation on every term.",
            check_question="Which term will you check next?",
            source_ids=tuple(source.source_id for source in sources[:1]),
            confidence=0.9,
            teacher_review_required=False,
            provider="capturing-test-provider",
        )


class FailingRetriever:
    def retrieve(self, request):
        del request
        raise AIIntegrationError("retrieval unavailable")


class FailingTutorGenerator(TutorGenerationPort):
    def generate(self, *, request, sources):
        del request, sources
        raise AIIntegrationError("model unavailable")


class InvalidTutorGenerator(TutorGenerationPort):
    def generate(self, *, request, sources):
        del sources
        return TutorDraft(
            mode=request.mode,
            message="The answer is revealed here.",
            check_question="What did you get?",
            source_ids=("unsupported-source",),
            confidence=0.9,
            teacher_review_required=False,
            answer_revealed=True,
            provider="invalid-test-provider",
        )


class FailingTutorFallback(TutorGenerationPort):
    def generate(self, *, request, sources):
        del request, sources
        raise RuntimeError("fallback unavailable")


class FailingQuizFallback(QuizGenerationPort):
    def generate(self, *, request, sources):
        del request, sources
        raise RuntimeError("fallback unavailable")


class FailingAudit:
    def record(self, event):
        del event
        raise RuntimeError("audit unavailable")


class LearningSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concept = Concept(
            id="ALG-DIST-01",
            subject_id="maths-9",
            name="Distributive property",
        )
        self.source = RetrievedSource(
            source_id="lesson-algebra-distributive-01",
            subject_id="maths-9",
            concept_id=self.concept.id,
            title="Distributive property worked example",
            text="Multiply the outside factor by every term inside the bracket.",
            confidence=0.95,
        )
        self.concepts = InMemoryConceptCatalog((self.concept,))
        self.validator = StructuredLearningOutputValidator()
        self.audit = InMemoryAIAudit()

    def test_riya_receives_grounded_non_spoiler_tutor_hint(self) -> None:
        use_case = self._tutor_use_case(
            retriever=InMemoryLearningRetriever((self.source,)),
        )

        result = use_case.execute(
            ProvideTutorSupportCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode="hint",
                misconception="negative sign not distributed",
            )
        )

        self.assertFalse(result.fallback_used)
        self.assertEqual(result.draft.source_ids, (self.source.source_id,))
        self.assertFalse(result.draft.answer_revealed)
        self.assertTrue(result.draft.check_question)
        self.assertFalse(self.audit.events[result.audit_event_id].fallback_used)

    def test_missing_retrieval_falls_back_and_requires_teacher_review(self) -> None:
        use_case = self._tutor_use_case(
            retriever=InMemoryLearningRetriever(()),
        )

        result = use_case.execute(
            ProvideTutorSupportCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode="hint",
            )
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.draft.provider, "curated-fallback")
        self.assertTrue(result.draft.teacher_review_required)
        self.assertEqual(result.draft.source_ids, ())
        self.assertIn("no_approved_source", self.audit.events[result.audit_event_id].validation_flags)

    def test_generator_failure_falls_back_without_stopping_support_flow(self) -> None:
        use_case = ProvideTutorSupport(
            concepts=self.concepts,
            retriever=InMemoryLearningRetriever((self.source,)),
            generator=FailingTutorGenerator(),
            fallback_generator=CuratedTutorFallback(),
            validator=self.validator,
            audit=self.audit,
        )

        result = use_case.execute(
            ProvideTutorSupportCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode="hint",
            )
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.draft.provider, "curated-fallback")
        self.assertIn("generated_output_failed", self.audit.events[result.audit_event_id].validation_flags)

    def test_invalid_generated_output_falls_back_before_reaching_learner(self) -> None:
        use_case = ProvideTutorSupport(
            concepts=self.concepts,
            retriever=InMemoryLearningRetriever((self.source,)),
            generator=InvalidTutorGenerator(),
            fallback_generator=CuratedTutorFallback(),
            validator=self.validator,
            audit=self.audit,
        )

        result = use_case.execute(
            ProvideTutorSupportCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode=TutorMode.HINT,
            )
        )

        self.assertTrue(result.fallback_used)
        self.assertFalse(result.draft.answer_revealed)
        self.assertEqual(result.draft.provider, "curated-fallback")

    def test_fallback_failure_returns_emergency_tutor_without_raising(self) -> None:
        use_case = ProvideTutorSupport(
            concepts=self.concepts,
            retriever=InMemoryLearningRetriever(()),
            generator=DeterministicTutorGenerator(),
            fallback_generator=FailingTutorFallback(),
            validator=self.validator,
            audit=self.audit,
        )

        result = use_case.execute(
            ProvideTutorSupportCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode=TutorMode.HINT,
            )
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.draft.provider, "emergency-fallback")
        self.assertIn("fallback_failed", self.audit.events[result.audit_event_id].validation_flags)

    def test_audit_failure_does_not_block_tutor_response(self) -> None:
        use_case = self._tutor_use_case(retriever=InMemoryLearningRetriever((self.source,)))
        use_case._audit = FailingAudit()  # type: ignore[assignment]

        result = use_case.execute(
            ProvideTutorSupportCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode=TutorMode.HINT,
            )
        )

        self.assertEqual(result.audit_event_id, "audit-unavailable")
        self.assertFalse(result.fallback_used)

    def test_weak_area_quiz_is_aligned_and_audited(self) -> None:
        use_case = GenerateWeakAreaQuiz(
            concepts=self.concepts,
            retriever=InMemoryLearningRetriever((self.source,)),
            generator=DeterministicQuizGenerator(),
            fallback_generator=CuratedQuizFallback(),
            validator=self.validator,
            audit=self.audit,
        )

        result = use_case.execute(
            GenerateWeakAreaQuizCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                difficulty=Difficulty.MEDIUM,
                item_count=3,
                misconception="negative sign not distributed",
            )
        )

        self.assertFalse(result.fallback_used)
        self.assertEqual(len(result.draft.items), 3)
        self.assertTrue(all(item.concept_id == self.concept.id for item in result.draft.items))
        self.assertEqual(result.draft.source_ids, (self.source.source_id,))
        self.assertEqual(self.audit.events[result.audit_event_id].event_type, "weak_area_quiz")

    def test_weak_area_quiz_falls_back_when_retrieval_provider_fails(self) -> None:
        use_case = GenerateWeakAreaQuiz(
            concepts=self.concepts,
            retriever=FailingRetriever(),
            generator=DeterministicQuizGenerator(),
            fallback_generator=CuratedQuizFallback(),
            validator=self.validator,
            audit=self.audit,
        )

        result = use_case.execute(
            GenerateWeakAreaQuizCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                difficulty=Difficulty.EASY,
                item_count=2,
            )
        )

        self.assertTrue(result.fallback_used)
        self.assertTrue(result.draft.teacher_review_required)
        self.assertEqual(len(result.draft.items), 2)
        self.assertEqual(result.draft.source_ids, ())

    def test_quiz_fallback_failure_returns_emergency_quiz_without_raising(self) -> None:
        use_case = GenerateWeakAreaQuiz(
            concepts=self.concepts,
            retriever=FailingRetriever(),
            generator=DeterministicQuizGenerator(),
            fallback_generator=FailingQuizFallback(),
            validator=self.validator,
            audit=self.audit,
        )

        result = use_case.execute(
            GenerateWeakAreaQuizCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                difficulty=Difficulty.MEDIUM,
                item_count=2,
            )
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(result.draft.provider, "emergency-fallback")
        self.assertTrue(result.draft.items[-1].is_transfer)

    def test_tutor_uses_persisted_misconception_and_evidence_context(self) -> None:
        attempts = InMemoryAttempts()
        for index in range(1, 3):
            attempts.record_attempt(
                "learner-riya",
                AttemptEvidence(
                    id=f"riya-{index}",
                    item_id=f"item-riya-{index}",
                    concept_id=self.concept.id,
                    is_correct=False,
                    difficulty=Difficulty.MEDIUM,
                    hint_count=2,
                    misconception="negative sign not distributed",
                ),
            )
        generator = CapturingTutorGenerator()
        use_case = ProvideTutorSupport(
            concepts=self.concepts,
            retriever=InMemoryLearningRetriever((self.source,)),
            generator=generator,
            fallback_generator=CuratedTutorFallback(),
            validator=self.validator,
            audit=self.audit,
            attempts=attempts,
            mastery_states=InMemoryMasteryStates(),
        )

        result = use_case.execute(
            ProvideTutorSupportCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                mode=TutorMode.HINT,
                misconception="caller supplied stale label",
            )
        )

        request = generator.requests[0]
        self.assertFalse(result.fallback_used)
        self.assertEqual(request.misconception, "negative sign not distributed")
        self.assertEqual(request.evidence_ids, ("riya-1", "riya-2"))
        self.assertEqual(request.evidence_count, 2)
        self.assertEqual(request.gap_status, "needs_support")
        self.assertEqual(result.evidence_reference_ids, ("riya-1", "riya-2"))

    def test_weak_area_quiz_scaffolds_persisted_weak_evidence(self) -> None:
        attempts = InMemoryAttempts()
        for index in range(1, 3):
            attempts.record_attempt(
                "learner-riya",
                AttemptEvidence(
                    id=f"weak-{index}",
                    item_id=f"item-weak-{index}",
                    concept_id=self.concept.id,
                    is_correct=False,
                    difficulty=Difficulty.MEDIUM,
                    hint_count=2,
                ),
            )
        use_case = GenerateWeakAreaQuiz(
            concepts=self.concepts,
            retriever=InMemoryLearningRetriever((self.source,)),
            generator=DeterministicQuizGenerator(),
            fallback_generator=CuratedQuizFallback(),
            validator=self.validator,
            audit=self.audit,
            attempts=attempts,
            mastery_states=InMemoryMasteryStates(),
        )

        result = use_case.execute(
            GenerateWeakAreaQuizCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id=self.concept.id,
                difficulty=Difficulty.HARD,
                item_count=2,
            )
        )

        self.assertEqual(result.effective_difficulty, Difficulty.EASY)
        self.assertTrue(all(item.difficulty is Difficulty.EASY for item in result.draft.items))
        self.assertEqual(result.evidence_reference_ids, ("weak-1", "weak-2"))

    def _tutor_use_case(self, *, retriever) -> ProvideTutorSupport:
        return ProvideTutorSupport(
            concepts=self.concepts,
            retriever=retriever,
            generator=DeterministicTutorGenerator(),
            fallback_generator=CuratedTutorFallback(),
            validator=self.validator,
            audit=self.audit,
        )


if __name__ == "__main__":
    unittest.main()
