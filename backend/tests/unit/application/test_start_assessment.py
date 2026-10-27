"""Tests for the StartAssessment application use case."""

from __future__ import annotations

import unittest

from backend.app.application.use_cases.start_assessment import (
    StartAssessment,
    StartAssessmentCommand,
)
from backend.app.domain.entities.learning import (
    AssessmentItem,
    AssessmentSession,
    Concept,
    Difficulty,
)


class InMemoryLearners:
    def __init__(self, learner_ids: set[str]) -> None:
        self.learner_ids = learner_ids

    def exists(self, learner_id: str) -> bool:
        return learner_id in self.learner_ids


class InMemoryConceptCatalog:
    def __init__(self, concepts_by_subject: dict[str, tuple[Concept, ...]]) -> None:
        self.concepts_by_subject = concepts_by_subject

    def list_concepts(self, subject_id: str) -> tuple[Concept, ...]:
        return self.concepts_by_subject.get(subject_id, ())


class InMemoryItemCatalog:
    def __init__(self, items_by_subject: dict[str, tuple[AssessmentItem, ...]]) -> None:
        self.items_by_subject = items_by_subject

    def list_items(self, subject_id: str) -> tuple[AssessmentItem, ...]:
        return self.items_by_subject.get(subject_id, ())

    def get_item(self, item_id: str) -> AssessmentItem | None:
        return next(
            (
                item
                for items in self.items_by_subject.values()
                for item in items
                if item.id == item_id
            ),
            None,
        )


class InMemorySessions:
    def __init__(self) -> None:
        self.sessions: list[AssessmentSession] = []

    def has_active_session(self, learner_id: str, subject_id: str) -> bool:
        return any(
            session.learner_id == learner_id
            and session.subject_id == subject_id
            and session.status.value == "active"
            for session in self.sessions
        )

    def create_session(self, session: AssessmentSession) -> None:
        self.sessions.append(session)

    def get_session(self, session_id: str) -> AssessmentSession | None:
        return next((session for session in self.sessions if session.id == session_id), None)

    def update_session(self, session: AssessmentSession) -> None:
        for index, existing in enumerate(self.sessions):
            if existing.id == session.id:
                self.sessions[index] = session
                return
        raise ValueError(f"unknown session: {session.id}")


class InMemorySessionIds:
    def __init__(self) -> None:
        self.next_number = 1
        self.calls = 0

    def next_id(self) -> str:
        self.calls += 1
        session_id = f"session-{self.next_number}"
        self.next_number += 1
        return session_id


class StartAssessmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root_concept = Concept(
            id="ALG-VAR-01",
            subject_id="maths-9",
            name="Variables and expressions",
        )
        self.dependent_concept = Concept(
            id="ALG-DIST-01",
            subject_id="maths-9",
            name="Distributive property",
            prerequisite_ids=(self.root_concept.id,),
        )
        self.learners = InMemoryLearners({"learner-riya", "learner-arjun"})
        self.catalog = InMemoryConceptCatalog(
            {"maths-9": (self.dependent_concept, self.root_concept)}
        )
        self.items = InMemoryItemCatalog(
            {
                "maths-9": (
                    AssessmentItem(
                        id="item-hard",
                        subject_id="maths-9",
                        concept_id=self.root_concept.id,
                        difficulty=Difficulty.HARD,
                        question="Solve a transfer equation.",
                        answer="x = 4",
                    ),
                    AssessmentItem(
                        id="item-medium",
                        subject_id="maths-9",
                        concept_id=self.root_concept.id,
                        difficulty=Difficulty.MEDIUM,
                        question="Solve x + 3 = 7.",
                        answer="x = 4",
                    ),
                    AssessmentItem(
                        id="item-dependent",
                        subject_id="maths-9",
                        concept_id=self.dependent_concept.id,
                        difficulty=Difficulty.EASY,
                        question="Expand 2(x + 1).",
                        answer="2x + 2",
                    ),
                )
            }
        )
        self.sessions = InMemorySessions()
        self.session_ids = InMemorySessionIds()
        self.use_case = StartAssessment(
            learners=self.learners,
            concepts=self.catalog,
            items=self.items,
            sessions=self.sessions,
            session_ids=self.session_ids,
        )

    def test_start_assessment_creates_active_session_at_root_concept(self) -> None:
        result = self.use_case.execute(
            StartAssessmentCommand(learner_id="learner-riya", subject_id="maths-9")
        )

        self.assertEqual(result.session.id, "session-1")
        self.assertEqual(result.session.learner_id, "learner-riya")
        self.assertEqual(result.session.subject_id, "maths-9")
        self.assertEqual(result.session.current_concept_id, self.root_concept.id)
        self.assertEqual(result.session.status.value, "active")
        self.assertEqual(result.initial_concept, self.root_concept)
        self.assertEqual(result.initial_item.id, "item-medium")
        self.assertEqual(result.initial_item.concept_id, result.initial_concept.id)
        self.assertEqual(self.sessions.sessions, [result.session])
        self.assertEqual(self.session_ids.calls, 1)

    def test_unknown_learner_does_not_create_session_or_consume_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown learner"):
            self.use_case.execute(
                StartAssessmentCommand(learner_id="learner-missing", subject_id="maths-9")
            )

        self.assertEqual(self.sessions.sessions, [])
        self.assertEqual(self.session_ids.calls, 0)

    def test_missing_approved_item_does_not_create_session_or_consume_id(self) -> None:
        self.items.items_by_subject["maths-9"] = (
            AssessmentItem(
                id="item-unapproved",
                subject_id="maths-9",
                concept_id=self.root_concept.id,
                difficulty=Difficulty.MEDIUM,
                question="Draft item.",
                answer="x = 1",
                approved=False,
            ),
        )

        with self.assertRaisesRegex(ValueError, "no approved assessment item"):
            self.use_case.execute(
                StartAssessmentCommand(learner_id="learner-riya", subject_id="maths-9")
            )

        self.assertEqual(self.sessions.sessions, [])
        self.assertEqual(self.session_ids.calls, 0)

    def test_unknown_subject_does_not_create_session_or_consume_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown subject"):
            self.use_case.execute(
                StartAssessmentCommand(learner_id="learner-riya", subject_id="science-9")
            )

        self.assertEqual(self.sessions.sessions, [])
        self.assertEqual(self.session_ids.calls, 0)

    def test_duplicate_active_session_is_rejected_before_new_id(self) -> None:
        first = self.use_case.execute(
            StartAssessmentCommand(learner_id="learner-arjun", subject_id="maths-9")
        )

        with self.assertRaisesRegex(ValueError, "active assessment"):
            self.use_case.execute(
                StartAssessmentCommand(learner_id="learner-arjun", subject_id="maths-9")
            )

        self.assertEqual(self.sessions.sessions, [first.session])
        self.assertEqual(self.session_ids.calls, 1)

    def test_empty_command_fields_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            StartAssessmentCommand(learner_id=" ", subject_id="maths-9")
        with self.assertRaises(ValueError):
            StartAssessmentCommand(learner_id="learner-riya", subject_id=" ")


if __name__ == "__main__":
    unittest.main()
