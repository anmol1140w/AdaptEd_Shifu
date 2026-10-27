"""Tests for reusable in-memory catalog and persistence adapters."""

from __future__ import annotations

import unittest

from backend.app.domain.entities.learning import (
    AssessmentItem,
    AssessmentSession,
    AttemptEvidence,
    Concept,
    Difficulty,
    MasteryState,
    Recommendation,
    Trend,
)
from backend.app.infrastructure.in_memory import (
    InMemoryAssessmentSessions,
    InMemoryAttempts,
    InMemoryConceptCatalog,
    InMemoryItemCatalog,
    InMemoryLearners,
    InMemoryMasteryStates,
    InMemoryRecommendations,
    InMemorySessionIds,
)


class InMemoryAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concept = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
        )
        self.item = AssessmentItem(
            id="item-eq",
            subject_id="maths-9",
            concept_id=self.concept.id,
            difficulty=Difficulty.MEDIUM,
            question="Solve x + 3 = 7.",
            answer="x = 4",
        )

    def test_catalogs_return_stable_sorted_content_and_reject_duplicate_ids(self) -> None:
        second_concept = Concept(
            id="ALG-VAR-01",
            subject_id="maths-9",
            name="Variables and expressions",
        )
        catalog = InMemoryConceptCatalog((self.concept, second_concept))
        self.assertEqual(
            tuple(concept.id for concept in catalog.list_concepts("maths-9")),
            ("ALG-EQ-02", "ALG-VAR-01"),
        )

        item_catalog = InMemoryItemCatalog((self.item,))
        self.assertEqual(item_catalog.get_item(self.item.id), self.item)
        self.assertEqual(item_catalog.list_items("science-9"), ())

        with self.assertRaisesRegex(ValueError, "concept IDs"):
            InMemoryConceptCatalog((self.concept, self.concept))
        with self.assertRaisesRegex(ValueError, "assessment item IDs"):
            InMemoryItemCatalog((self.item, self.item))

    def test_session_and_id_adapters_preserve_lifecycle(self) -> None:
        session_ids = InMemorySessionIds(prefix="demo")
        self.assertEqual(session_ids.next_id(), "demo-1")
        self.assertEqual(session_ids.next_id(), "demo-2")

        sessions = InMemoryAssessmentSessions()
        session = AssessmentSession(
            id="demo-1",
            learner_id="learner-riya",
            subject_id="maths-9",
            current_concept_id=self.concept.id,
        )
        sessions.create_session(session)
        self.assertTrue(sessions.has_active_session("learner-riya", "maths-9"))
        self.assertEqual(sessions.get_session(session.id), session)
        updated = AssessmentSession(
            id=session.id,
            learner_id=session.learner_id,
            subject_id=session.subject_id,
            current_concept_id="ALG-NEXT-01",
        )
        sessions.update_session(updated)
        self.assertEqual(sessions.get_session(session.id), updated)

        with self.assertRaisesRegex(ValueError, "already exists"):
            sessions.create_session(session)
        with self.assertRaisesRegex(ValueError, "unknown assessment session"):
            sessions.update_session(
                AssessmentSession(
                    id="missing",
                    learner_id="learner-riya",
                    subject_id="maths-9",
                    current_concept_id=self.concept.id,
                )
            )

    def test_learning_adapters_return_defensive_sequences_and_latest_recommendation(self) -> None:
        attempts = InMemoryAttempts()
        attempt = AttemptEvidence(
            id="attempt-1",
            item_id=self.item.id,
            concept_id=self.concept.id,
            is_correct=True,
            difficulty=self.item.difficulty,
        )
        attempts.record_attempt("learner-arjun", attempt)
        grouped = attempts.list_attempts("learner-arjun")
        self.assertEqual(grouped[self.concept.id], (attempt,))
        self.assertIsInstance(grouped[self.concept.id], tuple)
        with self.assertRaisesRegex(ValueError, "already exists"):
            attempts.record_attempt("learner-arjun", attempt)

        mastery = InMemoryMasteryStates()
        state = MasteryState(
            concept_id=self.concept.id,
            score=0.8,
            confidence=0.75,
            evidence_count=3,
            trend=Trend.STABLE,
            likely_misconception=None,
            recent_correctness=1.0,
            independence_score=1.0,
        )
        mastery.save_state("learner-arjun", state)
        self.assertEqual(mastery.get_states("learner-arjun")[self.concept.id], state)

        recommendations = InMemoryRecommendations()
        first = Recommendation(
            action_type="baseline_check",
            target_concept_id=self.concept.id,
            reason="Collect more evidence.",
            evidence_ids=(attempt.id,),
        )
        second = Recommendation(
            action_type="transfer_practice",
            target_concept_id=self.concept.id,
            reason="Test transfer.",
            evidence_ids=(attempt.id,),
        )
        recommendations.save_recommendation("learner-arjun", first)
        recommendations.save_recommendation("learner-arjun", second)
        self.assertEqual(recommendations.list_recommendations("learner-arjun"), (first, second))
        self.assertEqual(recommendations.latest("learner-arjun"), second)

    def test_learner_adapter_uses_known_ids_only(self) -> None:
        learners = InMemoryLearners({"learner-riya"})
        self.assertTrue(learners.exists("learner-riya"))
        self.assertFalse(learners.exists("learner-missing"))


if __name__ == "__main__":
    unittest.main()
