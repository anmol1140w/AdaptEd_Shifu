"""End-to-end in-memory tests for the framework-independent assessment facade."""

from __future__ import annotations

import unittest
from collections import defaultdict

from backend.app.application.assessment_facade import AssessmentFacade
from backend.app.application.use_cases.prepare_attempt import PrepareAttempt
from backend.app.application.use_cases.start_assessment import StartAssessment
from backend.app.application.use_cases.submit_attempt import SubmitAttempt
from backend.app.domain.entities.learning import (
    AssessmentItem,
    AssessmentSession,
    AssessmentSessionStatus,
    AttemptEvidence,
    Concept,
    Difficulty,
    MasteryState,
    Recommendation,
)
from backend.app.domain.services.learning_engine import LearningEngine
from backend.app.infrastructure.assessment.grading import DeterministicAssessmentGrader


class InMemoryLearners:
    def __init__(self, learner_ids: set[str]) -> None:
        self.learner_ids = learner_ids

    def exists(self, learner_id: str) -> bool:
        return learner_id in self.learner_ids


class InMemoryConceptCatalog:
    def __init__(self, concepts: tuple[Concept, ...]) -> None:
        self.concepts = concepts

    def list_concepts(self, subject_id: str) -> tuple[Concept, ...]:
        return tuple(concept for concept in self.concepts if concept.subject_id == subject_id)


class InMemoryItemCatalog:
    def __init__(self, items: tuple[AssessmentItem, ...]) -> None:
        self.items = {item.id: item for item in items}

    def list_items(self, subject_id: str) -> tuple[AssessmentItem, ...]:
        return tuple(item for item in self.items.values() if item.subject_id == subject_id)

    def get_item(self, item_id: str) -> AssessmentItem | None:
        return self.items.get(item_id)


class InMemorySessions:
    def __init__(self) -> None:
        self.data: dict[str, AssessmentSession] = {}

    def has_active_session(self, learner_id: str, subject_id: str) -> bool:
        return any(
            session.learner_id == learner_id
            and session.subject_id == subject_id
            and session.status is AssessmentSessionStatus.ACTIVE
            for session in self.data.values()
        )

    def create_session(self, session: AssessmentSession) -> None:
        self.data[session.id] = session

    def get_session(self, session_id: str) -> AssessmentSession | None:
        return self.data.get(session_id)

    def update_session(self, session: AssessmentSession) -> None:
        self.data[session.id] = session


class InMemorySessionIds:
    def __init__(self) -> None:
        self.next_number = 1

    def next_id(self) -> str:
        session_id = f"session-{self.next_number}"
        self.next_number += 1
        return session_id


class InMemoryAttempts:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, list[AttemptEvidence]]] = defaultdict(dict)
        self.recorded: list[tuple[str, AttemptEvidence]] = []

    def list_attempts(self, learner_id: str) -> dict[str, tuple[AttemptEvidence, ...]]:
        return {
            concept_id: tuple(attempts)
            for concept_id, attempts in self.data[learner_id].items()
        }

    def record_attempt(self, learner_id: str, attempt: AttemptEvidence) -> None:
        self.data[learner_id].setdefault(attempt.concept_id, []).append(attempt)
        self.recorded.append((learner_id, attempt))


class InMemoryMasteryStates:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, MasteryState]] = defaultdict(dict)

    def get_states(self, learner_id: str) -> dict[str, MasteryState]:
        return dict(self.data[learner_id])

    def save_state(self, learner_id: str, state: MasteryState) -> None:
        self.data[learner_id][state.concept_id] = state


class InMemoryRecommendations:
    def __init__(self) -> None:
        self.saved: list[tuple[str, Recommendation]] = []

    def save_recommendation(
        self,
        learner_id: str,
        recommendation: Recommendation,
    ) -> None:
        self.saved.append((learner_id, recommendation))


class AssessmentFacadeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concept = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
        )
        self.medium_item = AssessmentItem(
            id="item-medium",
            subject_id="maths-9",
            concept_id=self.concept.id,
            difficulty=Difficulty.MEDIUM,
            question="Solve x + 3 = 7.",
            answer="x = 4",
            misconception_tag="did not isolate the constant",
        )
        self.hard_item = AssessmentItem(
            id="item-hard",
            subject_id="maths-9",
            concept_id=self.concept.id,
            difficulty=Difficulty.HARD,
            question="Solve 3(x - 2) + 5 = 41.",
            answer="x = 14",
        )
        self.learners = InMemoryLearners({"learner-riya", "learner-arjun"})
        self.concepts = InMemoryConceptCatalog((self.concept,))
        self.items = InMemoryItemCatalog((self.medium_item, self.hard_item))
        self.sessions = InMemorySessions()
        self.attempts = InMemoryAttempts()
        self.mastery_states = InMemoryMasteryStates()
        self.recommendations = InMemoryRecommendations()
        engine = LearningEngine((self.concept,))
        self.facade = AssessmentFacade(
            start_assessment=StartAssessment(
                learners=self.learners,
                concepts=self.concepts,
                items=self.items,
                sessions=self.sessions,
                session_ids=InMemorySessionIds(),
            ),
            prepare_attempt=PrepareAttempt(
                items=self.items,
                grader=DeterministicAssessmentGrader(),
            ),
            submit_attempt=SubmitAttempt(
                learning_engine=engine,
                sessions=self.sessions,
                items=self.items,
                attempts=self.attempts,
                mastery_states=self.mastery_states,
                recommendations=self.recommendations,
            ),
            concepts=self.concepts,
            items=self.items,
            attempts=self.attempts,
            subject_names={"maths-9": "Class 9 Mathematics"},
        )

    def test_riya_receives_targeted_practice_and_teacher_review(self) -> None:
        started = self.facade.start(self._start_payload("learner-riya"))
        session_id = started["session"]["id"]

        first = self.facade.submit(
            self._submit_payload(
                learner_id="learner-riya",
                session_id=session_id,
                attempt_id="riya-1",
                item_id=self.medium_item.id,
                answer="x = 5",
                hint_count=2,
            )
        )
        second = self.facade.submit(
            self._submit_payload(
                learner_id="learner-riya",
                session_id=session_id,
                attempt_id="riya-2",
                item_id=self.medium_item.id,
                answer="x = 6",
                hint_count=2,
            )
        )

        self.assertEqual(first["recommendation"]["action_type"], "baseline_check")
        self.assertEqual(second["gap_status"], "needs_support")
        self.assertEqual(second["recommendation"]["action_type"], "targeted_practice")
        self.assertTrue(second["recommendation"]["teacher_review_required"])
        self.assertEqual(second["mastery"]["evidence_count"], 2)
        self.assertEqual(
            second["recommendation"]["evidence_reference_ids"],
            ["riya-1", "riya-2"],
        )
        self.assertEqual(len(self.attempts.recorded), 2)

    def test_arjun_receives_transfer_practice_after_independent_success(self) -> None:
        started = self.facade.start(self._start_payload("learner-arjun"))
        session_id = started["session"]["id"]

        for index in range(1, 3):
            self.facade.submit(
                self._submit_payload(
                    learner_id="learner-arjun",
                    session_id=session_id,
                    attempt_id=f"arjun-{index}",
                    item_id=self.medium_item.id,
                    answer="x = 4",
                    confidence_signal=0.9,
                )
            )
        for index in range(3, 5):
            final = self.facade.submit(
                self._submit_payload(
                    learner_id="learner-arjun",
                    session_id=session_id,
                    attempt_id=f"arjun-{index}",
                    item_id=self.hard_item.id,
                    answer="x = 14",
                    confidence_signal=0.9,
                )
            )

        self.assertEqual(final["gap_status"], "secure")
        self.assertEqual(final["recommendation"]["action_type"], "transfer_practice")
        self.assertFalse(final["recommendation"]["teacher_review_required"])
        self.assertEqual(final["mastery"]["evidence_count"], 4)
        self.assertEqual(final["evidence"]["difficulty"], "hard")
        self.assertEqual(
            final["recommendation"]["evidence_reference_ids"],
            ["arjun-1", "arjun-2", "arjun-3", "arjun-4"],
        )

    def test_unknown_item_fails_before_submit_attempt_can_write(self) -> None:
        started = self.facade.start(self._start_payload("learner-riya"))

        with self.assertRaisesRegex(ValueError, "unknown assessment item"):
            self.facade.submit(
                self._submit_payload(
                    learner_id="learner-riya",
                    session_id=started["session"]["id"],
                    attempt_id="riya-unknown",
                    item_id="item-missing",
                    answer="x = 4",
                )
            )

        self.assertEqual(self.attempts.recorded, [])
        self.assertEqual(self.mastery_states.data["learner-riya"], {})
        self.assertEqual(self.recommendations.saved, [])

    @staticmethod
    def _start_payload(learner_id: str) -> dict[str, object]:
        return {
            "contract_version": "v1",
            "learner_id": learner_id,
            "subject_id": "maths-9",
        }

    @staticmethod
    def _submit_payload(
        *,
        learner_id: str,
        session_id: str,
        attempt_id: str,
        item_id: str,
        answer: str,
        hint_count: int = 0,
        confidence_signal: float | None = None,
    ) -> dict[str, object]:
        attempt: dict[str, object] = {
            "id": attempt_id,
            "item_id": item_id,
            "concept_id": "ALG-EQ-02",
            "answer": answer,
            "response_ms": 1000,
            "hint_count": hint_count,
        }
        if confidence_signal is not None:
            attempt["confidence_signal"] = confidence_signal
        return {
            "contract_version": "v1",
            "session_id": session_id,
            "learner_id": learner_id,
            "attempt": attempt,
        }


if __name__ == "__main__":
    unittest.main()
