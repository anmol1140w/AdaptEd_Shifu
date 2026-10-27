"""Behavior tests for the evidence-backed teacher intervention queue."""

from __future__ import annotations

import unittest

from backend.app.application.use_cases.build_intervention_queue import (
    BuildInterventionQueue,
    BuildInterventionQueueCommand,
    InterventionPriority,
)
from backend.app.domain.entities.learning import AttemptEvidence, Concept, Difficulty
from backend.app.infrastructure.in_memory import (
    InMemoryAttempts,
    InMemoryConceptCatalog,
    InMemoryLearners,
    InMemoryMasteryStates,
    InMemoryRecommendations,
)


class BuildInterventionQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.foundation = Concept(
            id="ALG-DIST-01",
            subject_id="maths-9",
            name="Distributive property",
        )
        self.equations = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
            prerequisite_ids=(self.foundation.id,),
        )
        self.learners = InMemoryLearners(("learner-riya", "learner-arjun"))
        self.attempts = InMemoryAttempts()
        self.states = InMemoryMasteryStates()
        self.recommendations = InMemoryRecommendations()
        self.queue = BuildInterventionQueue(
            learners=self.learners,
            concepts=InMemoryConceptCatalog((self.foundation, self.equations)),
            attempts=self.attempts,
            mastery_states=self.states,
            recommendations=self.recommendations,
        )

    def test_riya_is_high_priority_and_arjun_is_not_remediated(self) -> None:
        for index in range(1, 3):
            self._record(
                "learner-riya",
                f"riya-dist-{index}",
                self.foundation,
                correct=False,
                hints=2,
                misconception="negative sign not distributed",
            )
        for index in range(1, 3):
            self._record(
                "learner-riya",
                f"riya-eq-{index}",
                self.equations,
                correct=False,
                hints=1,
            )
        for index in range(1, 5):
            self._record(
                "learner-arjun",
                f"arjun-eq-{index}",
                self.equations,
                correct=True,
            )

        result = self.queue.execute(BuildInterventionQueueCommand(subject_id="maths-9"))

        self.assertEqual(len(result.interventions), 1)
        intervention = result.interventions[0]
        self.assertEqual(intervention.learner_id, "learner-riya")
        self.assertEqual(intervention.concept.id, self.foundation.id)
        self.assertEqual(intervention.priority, InterventionPriority.HIGH)
        self.assertEqual(intervention.gap_status.value, "prerequisite_blocked")
        self.assertEqual(intervention.repeated_error_count, 4)
        self.assertEqual(intervention.average_hint_count, 1.5)
        self.assertEqual(
            set(intervention.recommendation.evidence_ids),
            {"riya-dist-1", "riya-dist-2", "riya-eq-1", "riya-eq-2"},
        )

    def test_explicit_learner_filter_is_deterministic(self) -> None:
        self._record("learner-riya", "riya-1", self.foundation, correct=False, hints=2)
        self._record("learner-riya", "riya-2", self.foundation, correct=False, hints=2)

        result = self.queue.execute(
            BuildInterventionQueueCommand(
                subject_id="maths-9",
                learner_ids=("learner-riya",),
            )
        )

        self.assertTrue(result.interventions)
        self.assertTrue(all(item.learner_id == "learner-riya" for item in result.interventions))

    def _record(
        self,
        learner_id: str,
        attempt_id: str,
        concept: Concept,
        *,
        correct: bool,
        hints: int = 0,
        misconception: str | None = None,
    ) -> None:
        self.attempts.record_attempt(
            learner_id,
            AttemptEvidence(
                id=attempt_id,
                item_id=f"item-{attempt_id}",
                concept_id=concept.id,
                is_correct=correct,
                difficulty=Difficulty.MEDIUM,
                hint_count=hints,
                misconception=misconception,
            ),
        )


if __name__ == "__main__":
    unittest.main()
