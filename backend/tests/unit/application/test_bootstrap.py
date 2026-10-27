"""End-to-end tests for the assembled in-memory assessment runtime."""

from __future__ import annotations

import unittest

from backend.app.api.v1.routes.assessment import LearnerRequestContext
from backend.app.application.ports.ai import RetrievedSource
from backend.app.bootstrap import build_in_memory_assessment_runtime
from backend.app.domain.entities.learning import AssessmentItem, Concept, Difficulty


class InMemoryAssessmentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        concept = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
        )
        medium_item = AssessmentItem(
            id="item-medium",
            subject_id="maths-9",
            concept_id=concept.id,
            difficulty=Difficulty.MEDIUM,
            question="Solve x + 3 = 7.",
            answer="x = 4",
            misconception_tag="did not isolate the constant",
        )
        hard_item = AssessmentItem(
            id="item-hard",
            subject_id="maths-9",
            concept_id=concept.id,
            difficulty=Difficulty.HARD,
            question="Solve 3(x - 2) + 5 = 41.",
            answer="x = 14",
        )
        self.runtime = build_in_memory_assessment_runtime(
            learner_ids=("learner-riya", "learner-arjun"),
            concepts=(concept,),
            items=(medium_item, hard_item),
            subject_names={"maths-9": "Class 9 Mathematics"},
            session_id_prefix="runtime",
        )
        self.medium_item = medium_item
        self.hard_item = hard_item

    def test_runtime_persists_start_and_submit_results_through_api_adapter(self) -> None:
        context = LearnerRequestContext(principal_id="learner-riya")
        started = self.runtime.api.start(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
            },
            context=context,
        )

        self.assertEqual(started.status_code, 201)
        session_id = started.body["session"]["id"]
        self.assertIn(session_id, self.runtime.sessions.sessions)

        submitted = self.runtime.api.submit(
            {
                "contract_version": "v1",
                "session_id": session_id,
                "learner_id": "learner-riya",
                "attempt": {
                    "id": "riya-1",
                    "item_id": self.medium_item.id,
                    "concept_id": "ALG-EQ-02",
                    "answer": "x = 5",
                    "response_ms": 1100,
                    "hint_count": 2,
                },
            },
            context=context,
        )

        self.assertEqual(submitted.status_code, 200)
        self.assertFalse(submitted.body["evidence"]["is_correct"])
        self.assertEqual(
            self.runtime.attempts.list_attempts("learner-riya")["ALG-EQ-02"][0].id,
            "riya-1",
        )
        self.assertEqual(
            self.runtime.mastery_states.get_states("learner-riya")["ALG-EQ-02"].evidence_count,
            1,
        )
        self.assertIsNotNone(self.runtime.recommendations.latest("learner-riya"))

    def test_same_runtime_keeps_riya_and_arjun_paths_different(self) -> None:
        riya_context = LearnerRequestContext(principal_id="learner-riya")
        arjun_context = LearnerRequestContext(principal_id="learner-arjun")
        riya_start = self._start("learner-riya", riya_context)
        arjun_start = self._start("learner-arjun", arjun_context)

        for index in range(1, 3):
            riya_result = self._submit(
                learner_id="learner-riya",
                session_id=riya_start,
                context=riya_context,
                attempt_id=f"riya-{index}",
                item_id=self.medium_item.id,
                answer="x = 5",
                hint_count=2,
            )
        for index in range(1, 5):
            arjun_result = self._submit(
                learner_id="learner-arjun",
                session_id=arjun_start,
                context=arjun_context,
                attempt_id=f"arjun-{index}",
                item_id=self.hard_item.id if index >= 3 else self.medium_item.id,
                answer="x = 14" if index >= 3 else "x = 4",
            )

        self.assertEqual(riya_result.body["recommendation"]["action_type"], "targeted_practice")
        self.assertTrue(riya_result.body["recommendation"]["teacher_review_required"])
        self.assertEqual(arjun_result.body["gap_status"], "secure")
        self.assertEqual(arjun_result.body["recommendation"]["action_type"], "transfer_practice")
        self.assertEqual(
            self.runtime.mastery_states.get_states("learner-riya")["ALG-EQ-02"].evidence_count,
            2,
        )
        self.assertEqual(
            self.runtime.mastery_states.get_states("learner-arjun")["ALG-EQ-02"].evidence_count,
            4,
        )

    def test_runtime_exposes_subject_summary_with_concept_drilldown(self) -> None:
        context = LearnerRequestContext(principal_id="learner-riya")
        session_id = self._start("learner-riya", context)
        submitted = self._submit(
            learner_id="learner-riya",
            session_id=session_id,
            context=context,
            attempt_id="riya-summary-1",
            item_id=self.medium_item.id,
            answer="x = 5",
            hint_count=2,
        )
        self.assertEqual(submitted.status_code, 200)

        summary = self.runtime.api.summary(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
            },
            context=context,
        )

        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.body["summary"]["evidence_count"], 1)
        self.assertEqual(summary.body["summary"]["assessed_concept_count"], 1)
        self.assertEqual(summary.body["concepts"][0]["concept"]["id"], "ALG-EQ-02")
        self.assertEqual(summary.body["concepts"][0]["mastery"]["evidence_count"], 1)
        self.assertEqual(
            summary.body["concepts"][0]["evidence"][0]["id"],
            "riya-summary-1",
        )

    def test_runtime_exposes_grounded_tutor_and_weak_area_quiz_support(self) -> None:
        concept = Concept(
            id="ALG-DIST-01",
            subject_id="maths-9",
            name="Distributive property",
        )
        runtime = build_in_memory_assessment_runtime(
            learner_ids=("learner-riya",),
            concepts=(concept,),
            items=(
                AssessmentItem(
                    id="item-dist-medium",
                    subject_id="maths-9",
                    concept_id=concept.id,
                    difficulty=Difficulty.MEDIUM,
                    question="Expand -2(x + 3).",
                    answer="-2x - 6",
                ),
            ),
            subject_names={"maths-9": "Class 9 Mathematics"},
            sources=(
                RetrievedSource(
                    source_id="lesson-algebra-distributive-01",
                    subject_id="maths-9",
                    concept_id=concept.id,
                    title="Distributive property worked example",
                    text="Multiply the outside factor by every term inside the bracket.",
                    confidence=0.95,
                ),
            ),
        )
        context = LearnerRequestContext(principal_id="learner-riya")

        tutor = runtime.support_api.tutor(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
                "concept_id": concept.id,
                "mode": "hint",
                "misconception": "negative sign not distributed",
            },
            context=context,
        )
        quiz = runtime.support_api.weak_area_quiz(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
                "concept_id": concept.id,
                "difficulty": "medium",
                "item_count": 3,
                "misconception": "negative sign not distributed",
            },
            context=context,
        )

        self.assertEqual(tutor.status_code, 200)
        self.assertFalse(tutor.body["fallback_used"])
        self.assertEqual(tutor.body["source_ids"], ["lesson-algebra-distributive-01"])
        self.assertFalse(tutor.body["answer_revealed"])
        self.assertEqual(quiz.status_code, 200)
        self.assertFalse(quiz.body["fallback_used"])
        self.assertEqual(len(quiz.body["items"]), 3)
        self.assertTrue(all("answer" not in item for item in quiz.body["items"]))
        self.assertEqual(len(runtime.ai_audit.events), 2)

    def _start(self, learner_id: str, context: LearnerRequestContext) -> str:
        response = self.runtime.api.start(
            {
                "contract_version": "v1",
                "learner_id": learner_id,
                "subject_id": "maths-9",
            },
            context=context,
        )
        self.assertEqual(response.status_code, 201)
        return response.body["session"]["id"]

    def _submit(
        self,
        *,
        learner_id: str,
        session_id: str,
        context: LearnerRequestContext,
        attempt_id: str,
        item_id: str,
        answer: str,
        hint_count: int = 0,
    ):
        return self.runtime.api.submit(
            {
                "contract_version": "v1",
                "session_id": session_id,
                "learner_id": learner_id,
                "attempt": {
                    "id": attempt_id,
                    "item_id": item_id,
                    "concept_id": "ALG-EQ-02",
                    "answer": answer,
                    "response_ms": 1000,
                    "hint_count": hint_count,
                },
            },
            context=context,
        )


if __name__ == "__main__":
    unittest.main()
