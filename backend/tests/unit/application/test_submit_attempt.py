"""Tests for the SubmitAttempt application use case."""

from __future__ import annotations

import unittest
from collections import defaultdict

from backend.app.application.use_cases.submit_attempt import (
    SubmitAttempt,
    SubmitAttemptCommand,
)
from backend.app.domain.entities.learning import (
    ActionType,
    AttemptEvidence,
    AssessmentItem,
    AssessmentSession,
    AssessmentSessionStatus,
    Concept,
    Difficulty,
    MasteryState,
    Recommendation,
)
from backend.app.domain.services.learning_engine import LearningEngine


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
        self.saved: list[tuple[str, MasteryState]] = []

    def get_states(self, learner_id: str) -> dict[str, MasteryState]:
        return dict(self.data[learner_id])

    def save_state(self, learner_id: str, state: MasteryState) -> None:
        self.data[learner_id][state.concept_id] = state
        self.saved.append((learner_id, state))


class InMemoryRecommendations:
    def __init__(self) -> None:
        self.saved: list[tuple[str, Recommendation]] = []

    def save_recommendation(
        self,
        learner_id: str,
        recommendation: Recommendation,
    ) -> None:
        self.saved.append((learner_id, recommendation))


class InMemoryItemCatalog:
    def __init__(self, items: list[AssessmentItem]) -> None:
        self.items = {item.id: item for item in items}

    def list_items(self, subject_id: str) -> tuple[AssessmentItem, ...]:
        return tuple(item for item in self.items.values() if item.subject_id == subject_id)

    def get_item(self, item_id: str) -> AssessmentItem | None:
        return self.items.get(item_id)


class InMemoryAssessmentSessions:
    def __init__(self) -> None:
        self.data: dict[str, AssessmentSession] = {}
        self.updated: list[AssessmentSession] = []

    def get_session(self, session_id: str) -> AssessmentSession | None:
        return self.data.get(session_id)

    def has_active_session(self, learner_id: str, subject_id: str) -> bool:
        return any(
            session.learner_id == learner_id
            and session.subject_id == subject_id
            and session.status is AssessmentSessionStatus.ACTIVE
            for session in self.data.values()
        )

    def create_session(self, session: AssessmentSession) -> None:
        self.data[session.id] = session

    def update_session(self, session: AssessmentSession) -> None:
        self.data[session.id] = session
        self.updated.append(session)


class SubmitAttemptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concept = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
        )
        self.engine = LearningEngine((self.concept,))
        self.items = InMemoryItemCatalog(
            [
                AssessmentItem(
                    id="item-eq",
                    subject_id="maths-9",
                    concept_id=self.concept.id,
                    difficulty=Difficulty.MEDIUM,
                    question="Solve x + 3 = 7.",
                    answer="x = 4",
                ),
                AssessmentItem(
                    id="item-unapproved",
                    subject_id="maths-9",
                    concept_id=self.concept.id,
                    difficulty=Difficulty.MEDIUM,
                    question="Draft equation.",
                    answer="x = 2",
                    approved=False,
                ),
                AssessmentItem(
                    id="item-science",
                    subject_id="science-9",
                    concept_id=self.concept.id,
                    difficulty=Difficulty.MEDIUM,
                    question="A science item.",
                    answer="4",
                ),
                AssessmentItem(
                    id="item-hard",
                    subject_id="maths-9",
                    concept_id=self.concept.id,
                    difficulty=Difficulty.HARD,
                    question="Solve a harder equation.",
                    answer="x = 8",
                ),
                AssessmentItem(
                    id="item-unknown-concept",
                    subject_id="maths-9",
                    concept_id="ALG-UNKNOWN",
                    difficulty=Difficulty.MEDIUM,
                    question="Unknown concept item.",
                    answer="x = 1",
                ),
            ]
        )
        self.sessions = InMemoryAssessmentSessions()
        self.attempts = InMemoryAttempts()
        self.states = InMemoryMasteryStates()
        self.recommendations = InMemoryRecommendations()
        self.use_case = SubmitAttempt(
            learning_engine=self.engine,
            sessions=self.sessions,
            items=self.items,
            attempts=self.attempts,
            mastery_states=self.states,
            recommendations=self.recommendations,
        )

    def test_submit_attempt_evaluates_history_and_persists_result(self) -> None:
        learner_id = "learner-arjun"
        self.sessions.data["session-arjun"] = self._session(
            session_id="session-arjun",
            learner_id=learner_id,
        )
        self.attempts.data[learner_id][self.concept.id] = [
            self._attempt("eq-1", correct=True),
            self._attempt("eq-2", correct=True),
            self._attempt("eq-3", correct=True),
        ]

        result = self.use_case.execute(
            SubmitAttemptCommand(
                session_id="session-arjun",
                learner_id=learner_id,
                attempt=self._attempt("eq-4", correct=True),
            )
        )

        self.assertEqual(result.outcome.recommendation.action_type, ActionType.TRANSFER_PRACTICE)
        self.assertEqual(len(self.attempts.recorded), 1)
        self.assertEqual(self.attempts.recorded[0][1].id, "eq-4")
        self.assertEqual(len(self.states.saved), 1)
        self.assertEqual(self.states.saved[0][1].evidence_count, 4)
        self.assertEqual(len(self.recommendations.saved), 1)
        self.assertEqual(len(self.sessions.updated), 1)
        self.assertEqual(
            result.session.current_concept_id,
            self.concept.id,
        )

    def test_domain_failure_does_not_persist_partial_state(self) -> None:
        self.sessions.data["session-unknown"] = AssessmentSession(
            id="session-unknown",
            learner_id="learner-unknown",
            subject_id="maths-9",
            current_concept_id="ALG-UNKNOWN",
        )
        with self.assertRaises(ValueError):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-unknown",
                    learner_id="learner-unknown",
                    attempt=AttemptEvidence(
                        id="bad-1",
                        item_id="item-unknown-concept",
                        concept_id="ALG-UNKNOWN",
                        is_correct=True,
                        difficulty=Difficulty.MEDIUM,
                    ),
                )
            )

        self.assertEqual(self.attempts.recorded, [])
        self.assertEqual(self.states.saved, [])
        self.assertEqual(self.recommendations.saved, [])
        self.assertEqual(self.sessions.updated, [])

    def test_duplicate_attempt_id_is_rejected_before_domain_write(self) -> None:
        learner_id = "learner-riya"
        self.sessions.data["session-riya"] = self._session(
            session_id="session-riya",
            learner_id=learner_id,
        )
        existing = self._attempt("duplicate-1", correct=False)
        self.attempts.data[learner_id][self.concept.id] = [existing]

        with self.assertRaises(ValueError):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-riya",
                    learner_id=learner_id,
                    attempt=existing,
                )
            )

        self.assertEqual(self.attempts.recorded, [])
        self.assertEqual(self.states.saved, [])
        self.assertEqual(self.recommendations.saved, [])
        self.assertEqual(self.sessions.updated, [])

    def test_unknown_session_is_rejected_before_loading_attempts(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown assessment session"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-missing",
                    learner_id="learner-riya",
                    attempt=self._attempt("eq-1", correct=True),
                )
            )

        self.assertEqual(self.attempts.recorded, [])

    def test_unknown_item_is_rejected_before_domain_evaluation(self) -> None:
        self.sessions.data["session-riya"] = self._session(
            session_id="session-riya",
            learner_id="learner-riya",
        )

        with self.assertRaisesRegex(ValueError, "unknown assessment item"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-riya",
                    learner_id="learner-riya",
                    attempt=self._attempt("missing-item", correct=True, item_id="item-missing"),
                )
            )

        self.assertEqual(self.attempts.recorded, [])

    def test_unapproved_item_is_rejected(self) -> None:
        self.sessions.data["session-riya"] = self._session(
            session_id="session-riya",
            learner_id="learner-riya",
        )

        with self.assertRaisesRegex(ValueError, "not approved"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-riya",
                    learner_id="learner-riya",
                    attempt=self._attempt(
                        "unapproved-item",
                        correct=True,
                        item_id="item-unapproved",
                    ),
                )
            )

    def test_item_subject_and_difficulty_must_match_submission(self) -> None:
        self.sessions.data["session-riya"] = self._session(
            session_id="session-riya",
            learner_id="learner-riya",
        )

        with self.assertRaisesRegex(ValueError, "session subject"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-riya",
                    learner_id="learner-riya",
                    attempt=self._attempt(
                        "science-item",
                        correct=True,
                        item_id="item-science",
                    ),
                )
            )

        with self.assertRaisesRegex(ValueError, "difficulty"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-riya",
                    learner_id="learner-riya",
                    attempt=self._attempt(
                        "wrong-difficulty",
                        correct=True,
                        item_id="item-hard",
                    ),
                )
            )

    def test_inactive_or_wrong_learner_session_is_rejected(self) -> None:
        self.sessions.data["session-cancelled"] = self._session(
            session_id="session-cancelled",
            learner_id="learner-riya",
            status=AssessmentSessionStatus.CANCELLED,
        )
        with self.assertRaisesRegex(ValueError, "not active"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-cancelled",
                    learner_id="learner-riya",
                    attempt=self._attempt("eq-1", correct=True),
                )
            )

        self.sessions.data["session-owner"] = self._session(
            session_id="session-owner",
            learner_id="learner-arjun",
        )
        with self.assertRaisesRegex(ValueError, "does not belong"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-owner",
                    learner_id="learner-riya",
                    attempt=self._attempt("eq-2", correct=True),
                )
            )

    def test_attempt_concept_must_match_session_current_concept(self) -> None:
        other_concept = Concept(
            id="ALG-OTHER",
            subject_id="maths-9",
            name="Other concept",
        )
        other_attempt = AttemptEvidence(
            id="other-1",
            item_id="item-other",
            concept_id=other_concept.id,
            is_correct=True,
            difficulty=Difficulty.MEDIUM,
        )
        self.sessions.data["session-riya"] = self._session(
            session_id="session-riya",
            learner_id="learner-riya",
        )

        with self.assertRaisesRegex(ValueError, "does not match"):
            self.use_case.execute(
                SubmitAttemptCommand(
                    session_id="session-riya",
                    learner_id="learner-riya",
                    attempt=other_attempt,
                )
            )

    def test_empty_learner_id_is_rejected_at_command_boundary(self) -> None:
        with self.assertRaises(ValueError):
            SubmitAttemptCommand(
                session_id="session-1",
                learner_id=" ",
                attempt=self._attempt("eq-1", correct=True),
            )

        with self.assertRaises(ValueError):
            SubmitAttemptCommand(
                session_id=" ",
                learner_id="learner-riya",
                attempt=self._attempt("eq-2", correct=True),
            )

    def _attempt(
        self,
        attempt_id: str,
        *,
        correct: bool,
        item_id: str = "item-eq",
    ) -> AttemptEvidence:
        return AttemptEvidence(
            id=attempt_id,
            item_id=item_id,
            concept_id=self.concept.id,
            is_correct=correct,
            difficulty=Difficulty.MEDIUM,
        )

    def _session(
        self,
        *,
        session_id: str,
        learner_id: str,
        status: AssessmentSessionStatus = AssessmentSessionStatus.ACTIVE,
    ) -> AssessmentSession:
        return AssessmentSession(
            id=session_id,
            learner_id=learner_id,
            subject_id="maths-9",
            current_concept_id=self.concept.id,
            status=status,
        )


if __name__ == "__main__":
    unittest.main()
