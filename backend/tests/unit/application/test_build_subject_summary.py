"""Behavior tests for subject-level aggregation and concept drill-down."""

from __future__ import annotations

import unittest

from backend.app.application.use_cases.build_subject_summary import (
    BuildSubjectSummary,
    BuildSubjectSummaryCommand,
)
from backend.app.domain.entities.learning import AttemptEvidence, Concept, Difficulty, GapStatus
from backend.app.infrastructure.in_memory import (
    InMemoryAttempts,
    InMemoryConceptCatalog,
    InMemoryMasteryStates,
)


class BuildSubjectSummaryTests(unittest.TestCase):
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
        self.unassessed = Concept(
            id="ALG-VAR-03",
            subject_id="maths-9",
            name="Variables and expressions",
        )
        self.attempts = InMemoryAttempts()
        self.mastery_states = InMemoryMasteryStates()
        self.summary = BuildSubjectSummary(
            concepts=InMemoryConceptCatalog(
                (self.equations, self.unassessed, self.foundation)
            ),
            attempts=self.attempts,
            mastery_states=self.mastery_states,
        )

    def test_summary_keeps_concept_evidence_and_prerequisite_recommendation(self) -> None:
        self._record_incorrect("foundation-1", self.foundation.id)
        self._record_incorrect("foundation-2", self.foundation.id)
        self._record_incorrect("equations-1", self.equations.id)
        self._record_incorrect("equations-2", self.equations.id)

        result = self.summary.execute(
            BuildSubjectSummaryCommand(
                learner_id="learner-riya",
                subject_id="maths-9",
            )
        )

        self.assertEqual(
            [concept.concept.id for concept in result.concepts],
            ["ALG-DIST-01", "ALG-EQ-02", "ALG-VAR-03"],
        )
        self.assertEqual(result.evidence_count, 4)
        self.assertEqual(result.concepts[0].gap_status, GapStatus.NEEDS_SUPPORT)
        self.assertEqual(result.concepts[1].gap_status, GapStatus.PREREQUISITE_BLOCKED)
        self.assertEqual(
            result.concepts[1].recommendation.target_concept_id,
            self.foundation.id,
        )
        self.assertEqual(
            [attempt.id for attempt in result.concepts[1].evidence],
            ["equations-1", "equations-2"],
        )
        self.assertEqual(result.concepts[2].gap_status, GapStatus.NOT_ENOUGH_EVIDENCE)
        self.assertIsNone(result.concepts[2].mastery_state)
        self.assertEqual(
            dict(result.gap_status_counts)[GapStatus.NOT_ENOUGH_EVIDENCE],
            1,
        )

    def test_empty_subject_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty concept graph"):
            self.summary.execute(
                BuildSubjectSummaryCommand(
                    learner_id="learner-riya",
                    subject_id="science-9",
                )
            )

    def _record_incorrect(self, attempt_id: str, concept_id: str) -> None:
        self.attempts.record_attempt(
            "learner-riya",
            AttemptEvidence(
                id=attempt_id,
                item_id=f"item-{attempt_id}",
                concept_id=concept_id,
                is_correct=False,
                difficulty=Difficulty.MEDIUM,
                hint_count=2,
                misconception="negative sign not distributed",
            ),
        )


if __name__ == "__main__":
    unittest.main()
