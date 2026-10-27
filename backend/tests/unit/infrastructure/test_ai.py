"""Tests for provider-neutral mock AI adapters and validators."""

from __future__ import annotations

import unittest

from backend.app.application.ports.ai import (
    AIAuditEvent,
    AIValidationError,
    QuizRequest,
    RetrievedSource,
    RetrievalRequest,
    TutorDraft,
    TutorMode,
    TutorRequest,
)
from backend.app.domain.entities.learning import Difficulty
from backend.app.infrastructure.ai.audit import InMemoryAIAudit
from backend.app.infrastructure.ai.llm import (
    DeterministicQuizGenerator,
    DeterministicTutorGenerator,
)
from backend.app.infrastructure.ai.retrieval import InMemoryLearningRetriever
from backend.app.infrastructure.ai.validators import StructuredLearningOutputValidator


class AIAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = RetrievedSource(
            source_id="lesson-algebra-distributive-01",
            subject_id="maths-9",
            concept_id="ALG-DIST-01",
            title="Distributive property worked example",
            text="Multiply the outside factor by every term inside the bracket.",
            confidence=0.95,
        )
        self.retriever = InMemoryLearningRetriever((self.source,))
        self.validator = StructuredLearningOutputValidator()

    def test_retriever_returns_only_approved_matching_source(self) -> None:
        result = self.retriever.retrieve(
            RetrievalRequest(
                subject_id="maths-9",
                concept_id="ALG-DIST-01",
                query="negative sign distributive property",
            )
        )

        self.assertEqual([source.source_id for source in result.sources], [self.source.source_id])
        self.assertEqual(result.confidence, 0.95)

    def test_deterministic_tutor_is_grounded_and_non_spoiler(self) -> None:
        request = TutorRequest(
            learner_id="learner-riya",
            subject_id="maths-9",
            concept_id="ALG-DIST-01",
            mode=TutorMode.HINT,
            misconception="negative sign not distributed",
        )
        draft = DeterministicTutorGenerator().generate(
            request=request,
            sources=(self.source,),
        )

        self.validator.validate_tutor(request=request, draft=draft, sources=(self.source,))
        self.assertIn("negative multiplier", draft.message)
        self.assertEqual(draft.source_ids, (self.source.source_id,))
        self.assertFalse(draft.answer_revealed)
        self.assertIn("Which term", draft.check_question)

    def test_validator_rejects_spoiler_hint_and_unsupported_source(self) -> None:
        request = TutorRequest(
            learner_id="learner-riya",
            subject_id="maths-9",
            concept_id="ALG-DIST-01",
            mode=TutorMode.HINT,
        )
        spoiler = TutorDraft(
            mode=TutorMode.HINT,
            message="The answer is -2x - 6.",
            check_question="What did you get?",
            source_ids=("unapproved-source",),
            confidence=0.9,
            teacher_review_required=False,
            answer_revealed=True,
            provider="test",
        )

        with self.assertRaises(AIValidationError):
            self.validator.validate_tutor(
                request=request,
                draft=spoiler,
                sources=(self.source,),
            )

    def test_quiz_generator_keeps_requested_concept_and_count(self) -> None:
        request = QuizRequest(
            learner_id="learner-riya",
            subject_id="maths-9",
            concept_id="ALG-DIST-01",
            difficulty=Difficulty.MEDIUM,
            item_count=3,
            include_transfer=True,
        )
        draft = DeterministicQuizGenerator().generate(
            request=request,
            sources=(self.source,),
        )

        self.validator.validate_quiz(request=request, draft=draft, sources=(self.source,))
        self.assertEqual(len(draft.items), 3)
        self.assertTrue(all(item.concept_id == request.concept_id for item in draft.items))
        self.assertTrue(draft.items[-1].is_transfer)
        self.assertTrue(all(item.answer for item in draft.items))

    def test_audit_store_returns_stable_ids_and_defensive_events(self) -> None:
        audit = InMemoryAIAudit()
        event_id = audit.record(
            AIAuditEvent(
                event_type="tutor_response",
                learner_id="learner-riya",
                subject_id="maths-9",
                concept_id="ALG-DIST-01",
                provider="curated-fallback",
                fallback_used=True,
                source_ids=(),
                validation_flags=("no_approved_source",),
            )
        )

        self.assertEqual(event_id, "ai-audit-1")
        self.assertTrue(audit.events[event_id].fallback_used)


if __name__ == "__main__":
    unittest.main()
