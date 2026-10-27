"""Application orchestration for recording one learner attempt."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ...domain.entities.learning import (
    AssessmentSession,
    AssessmentSessionStatus,
    AttemptEvidence,
    LearningOutcome,
)
from ...domain.services.learning_engine import LearningEngine
from ..ports.assessment import AssessmentSessionPort, ItemCatalogPort
from ..ports.learning import AttemptPort, MasteryStatePort, RecommendationPort


@dataclass(frozen=True, slots=True)
class SubmitAttemptCommand:
    """Input required to evaluate and persist one learner attempt."""

    session_id: str
    learner_id: str
    attempt: AttemptEvidence

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session id must not be empty")
        if not self.learner_id.strip():
            raise ValueError("learner id must not be empty")


@dataclass(frozen=True, slots=True)
class SubmitAttemptResult:
    """Application result returned after a successful attempt submission."""

    session: AssessmentSession
    learner_id: str
    attempt: AttemptEvidence
    outcome: LearningOutcome


class SubmitAttempt:
    """Coordinate ports and the domain for one attempt submission."""

    def __init__(
        self,
        *,
        learning_engine: LearningEngine,
        sessions: AssessmentSessionPort,
        items: ItemCatalogPort,
        attempts: AttemptPort,
        mastery_states: MasteryStatePort,
        recommendations: RecommendationPort,
    ) -> None:
        self._learning_engine = learning_engine
        self._sessions = sessions
        self._items = items
        self._attempts = attempts
        self._mastery_states = mastery_states
        self._recommendations = recommendations

    def execute(self, command: SubmitAttemptCommand) -> SubmitAttemptResult:
        """Evaluate the new evidence, then persist the resulting state."""

        session = self._sessions.get_session(command.session_id)
        if session is None:
            raise ValueError(f"unknown assessment session: {command.session_id}")
        if session.status is not AssessmentSessionStatus.ACTIVE:
            raise ValueError(f"assessment session is not active: {command.session_id}")
        if session.learner_id != command.learner_id:
            raise ValueError("assessment session does not belong to learner")
        if session.current_concept_id != command.attempt.concept_id:
            raise ValueError(
                "attempt concept does not match the assessment session's current concept"
            )
        item = self._items.get_item(command.attempt.item_id)
        if item is None:
            raise ValueError(f"unknown assessment item: {command.attempt.item_id}")
        if not item.approved:
            raise ValueError(f"assessment item is not approved: {command.attempt.item_id}")
        if item.subject_id != session.subject_id:
            raise ValueError("assessment item does not belong to session subject")
        if item.concept_id != session.current_concept_id:
            raise ValueError("assessment item does not match the session's current concept")
        if item.difficulty is not command.attempt.difficulty:
            raise ValueError("attempt difficulty does not match assessment item")

        attempts_by_concept = {
            concept_id: tuple(concept_attempts)
            for concept_id, concept_attempts in self._attempts.list_attempts(
                command.learner_id
            ).items()
        }
        if self._contains_attempt_id(attempts_by_concept, command.attempt.id):
            raise ValueError(f"attempt already exists: {command.attempt.id}")

        current_attempts = attempts_by_concept.setdefault(command.attempt.concept_id, ())
        attempts_by_concept[command.attempt.concept_id] = (
            *current_attempts,
            command.attempt,
        )

        outcome = self._learning_engine.evaluate(
            focus_concept_id=command.attempt.concept_id,
            attempts_by_concept=attempts_by_concept,
            existing_states=self._mastery_states.get_states(command.learner_id),
        )

        self._attempts.record_attempt(command.learner_id, command.attempt)
        self._mastery_states.save_state(
            command.learner_id,
            outcome.mastery_state,
        )
        self._recommendations.save_recommendation(
            command.learner_id,
            outcome.recommendation,
        )
        next_session = replace(
            session,
            current_concept_id=outcome.recommendation.target_concept_id,
        )
        self._sessions.update_session(next_session)
        return SubmitAttemptResult(
            session=next_session,
            learner_id=command.learner_id,
            attempt=command.attempt,
            outcome=outcome,
        )

    @staticmethod
    def _contains_attempt_id(
        attempts_by_concept: dict[str, tuple[AttemptEvidence, ...]],
        attempt_id: str,
    ) -> bool:
        return any(
            attempt.id == attempt_id
            for attempts in attempts_by_concept.values()
            for attempt in attempts
        )
