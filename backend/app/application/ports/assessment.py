"""Ports required to start and persist assessment sessions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ...domain.entities.learning import AssessmentItem, AssessmentSession, Concept


class LearnerPort(Protocol):
    """Check whether a learner can start an assessment."""

    def exists(self, learner_id: str) -> bool:
        """Return whether the learner is known to the application."""
        ...


class ConceptCatalogPort(Protocol):
    """Load the approved concept graph for a subject."""

    def list_concepts(self, subject_id: str) -> Sequence[Concept]:
        """Return concepts available for the requested subject."""
        ...


class ItemCatalogPort(Protocol):
    """Load approved assessment items for a subject."""

    def list_items(self, subject_id: str) -> Sequence[AssessmentItem]:
        """Return assessment items available for the requested subject."""
        ...

    def get_item(self, item_id: str) -> AssessmentItem | None:
        """Return an assessment item by ID, or ``None`` when it does not exist."""
        ...


class AssessmentSessionPort(Protocol):
    """Check and persist assessment-session state."""

    def has_active_session(self, learner_id: str, subject_id: str) -> bool:
        """Return whether the learner already has an active subject session."""
        ...

    def create_session(self, session: AssessmentSession) -> None:
        """Persist a newly-created assessment session."""
        ...

    def get_session(self, session_id: str) -> AssessmentSession | None:
        """Return a session by ID, or ``None`` when it does not exist."""
        ...

    def update_session(self, session: AssessmentSession) -> None:
        """Persist the next state of an existing assessment session."""
        ...


class SessionIdPort(Protocol):
    """Generate identifiers without coupling the use case to a library."""

    def next_id(self) -> str:
        """Return a new unique assessment-session identifier."""
        ...
