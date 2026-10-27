"""Reusable in-memory adapters for the provider-neutral application ports."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence

from ..application.ports.assessment import (
    AssessmentSessionPort,
    ConceptCatalogPort,
    ItemCatalogPort,
    LearnerPort,
    SessionIdPort,
)
from ..application.ports.learning import (
    AttemptPort,
    MasteryStatePort,
    RecommendationPort,
)
from ..domain.entities.learning import (
    AssessmentItem,
    AssessmentSession,
    AssessmentSessionStatus,
    AttemptEvidence,
    Concept,
    MasteryState,
    Recommendation,
)


class InMemoryLearners(LearnerPort):
    """Store known learner identifiers for local execution."""

    def __init__(self, learner_ids: Iterable[str]) -> None:
        normalized = {learner_id for learner_id in learner_ids}
        if any(not learner_id.strip() for learner_id in normalized):
            raise ValueError("learner IDs must not be empty")
        self._learner_ids = normalized

    def exists(self, learner_id: str) -> bool:
        return learner_id in self._learner_ids


class InMemoryConceptCatalog(ConceptCatalogPort):
    """Read-only concept catalog indexed by subject and concept ID."""

    def __init__(self, concepts: Iterable[Concept]) -> None:
        concept_list = tuple(concepts)
        self._by_subject: dict[str, tuple[Concept, ...]] = {}
        for subject_id in {concept.subject_id for concept in concept_list}:
            subject_concepts = tuple(
                concept for concept in concept_list if concept.subject_id == subject_id
            )
            self._by_subject[subject_id] = tuple(
                sorted(subject_concepts, key=lambda concept: concept.id)
            )
        self._validate_unique_ids(concept_list)

    def list_concepts(self, subject_id: str) -> Sequence[Concept]:
        return self._by_subject.get(subject_id, ())

    @staticmethod
    def _validate_unique_ids(concepts: Sequence[Concept]) -> None:
        ids = [concept.id for concept in concepts]
        if len(ids) != len(set(ids)):
            raise ValueError("concept IDs must be unique")


class InMemoryItemCatalog(ItemCatalogPort):
    """Read-only assessment-item catalog indexed by stable item ID."""

    def __init__(self, items: Iterable[AssessmentItem]) -> None:
        item_list = tuple(items)
        ids = [item.id for item in item_list]
        if len(ids) != len(set(ids)):
            raise ValueError("assessment item IDs must be unique")
        self._items = {item.id: item for item in item_list}
        self._by_subject: dict[str, tuple[AssessmentItem, ...]] = {}
        for subject_id in {item.subject_id for item in item_list}:
            subject_items = tuple(
                item for item in item_list if item.subject_id == subject_id
            )
            self._by_subject[subject_id] = tuple(
                sorted(subject_items, key=lambda item: item.id)
            )

    def list_items(self, subject_id: str) -> Sequence[AssessmentItem]:
        return self._by_subject.get(subject_id, ())

    def get_item(self, item_id: str) -> AssessmentItem | None:
        return self._items.get(item_id)


class InMemoryAssessmentSessions(AssessmentSessionPort):
    """Mutable assessment-session store with stable IDs and active-session checks."""

    def __init__(self) -> None:
        self._sessions: dict[str, AssessmentSession] = {}

    def has_active_session(self, learner_id: str, subject_id: str) -> bool:
        return any(
            session.learner_id == learner_id
            and session.subject_id == subject_id
            and session.status is AssessmentSessionStatus.ACTIVE
            for session in self._sessions.values()
        )

    def create_session(self, session: AssessmentSession) -> None:
        if session.id in self._sessions:
            raise ValueError(f"assessment session already exists: {session.id}")
        self._sessions[session.id] = session

    def get_session(self, session_id: str) -> AssessmentSession | None:
        return self._sessions.get(session_id)

    def update_session(self, session: AssessmentSession) -> None:
        if session.id not in self._sessions:
            raise ValueError(f"unknown assessment session: {session.id}")
        self._sessions[session.id] = session

    @property
    def sessions(self) -> Mapping[str, AssessmentSession]:
        """Return a read-only view for local inspection and tests."""

        return dict(self._sessions)


class InMemorySessionIds(SessionIdPort):
    """Deterministically generate process-local session identifiers."""

    def __init__(self, *, prefix: str = "session") -> None:
        if not prefix.strip():
            raise ValueError("session ID prefix must not be empty")
        self._prefix = prefix
        self._next_number = 1

    def next_id(self) -> str:
        session_id = f"{self._prefix}-{self._next_number}"
        self._next_number += 1
        return session_id


class InMemoryAttempts(AttemptPort):
    """Mutable attempt store grouped by learner and concept."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, list[AttemptEvidence]]] = defaultdict(dict)

    def list_attempts(self, learner_id: str) -> Mapping[str, Sequence[AttemptEvidence]]:
        return {
            concept_id: tuple(attempts)
            for concept_id, attempts in self._data[learner_id].items()
        }

    def record_attempt(self, learner_id: str, attempt: AttemptEvidence) -> None:
        concept_attempts = self._data[learner_id].setdefault(attempt.concept_id, [])
        if any(existing.id == attempt.id for existing in concept_attempts):
            raise ValueError(f"attempt already exists: {attempt.id}")
        concept_attempts.append(attempt)


class InMemoryMasteryStates(MasteryStatePort):
    """Mutable mastery-state store keyed by learner and concept."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, MasteryState]] = defaultdict(dict)

    def get_states(self, learner_id: str) -> Mapping[str, MasteryState]:
        return dict(self._data[learner_id])

    def save_state(self, learner_id: str, state: MasteryState) -> None:
        self._data[learner_id][state.concept_id] = state


class InMemoryRecommendations(RecommendationPort):
    """Append-only recommendation history for local inspection."""

    def __init__(self) -> None:
        self._data: dict[str, list[Recommendation]] = defaultdict(list)

    def save_recommendation(
        self,
        learner_id: str,
        recommendation: Recommendation,
    ) -> None:
        self._data[learner_id].append(recommendation)

    def list_recommendations(self, learner_id: str) -> tuple[Recommendation, ...]:
        return tuple(self._data[learner_id])

    def latest(self, learner_id: str) -> Recommendation | None:
        recommendations = self._data[learner_id]
        return recommendations[-1] if recommendations else None
