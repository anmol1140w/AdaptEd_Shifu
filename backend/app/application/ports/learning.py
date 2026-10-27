"""Ports required by the learning application use cases."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from ...domain.entities.learning import AttemptEvidence, MasteryState, Recommendation


class AttemptPort(Protocol):
    """Load and record learner attempt evidence."""

    def list_attempts(
        self,
        learner_id: str,
    ) -> Mapping[str, Sequence[AttemptEvidence]]:
        """Return attempts grouped by concept for one learner."""
        ...

    def record_attempt(self, learner_id: str, attempt: AttemptEvidence) -> None:
        """Persist one attempt after the domain accepts it."""
        ...


class MasteryStatePort(Protocol):
    """Load and persist explainable mastery states."""

    def get_states(self, learner_id: str) -> Mapping[str, MasteryState]:
        """Return known mastery states for one learner."""
        ...

    def save_state(self, learner_id: str, state: MasteryState) -> None:
        """Persist one updated concept state."""
        ...


class RecommendationPort(Protocol):
    """Persist the latest recommendation produced for a learner."""

    def save_recommendation(
        self,
        learner_id: str,
        recommendation: Recommendation,
    ) -> None:
        """Persist one recommendation after successful domain evaluation."""
        ...
