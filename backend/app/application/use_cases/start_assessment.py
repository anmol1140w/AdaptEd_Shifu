"""Application orchestration for starting an assessment session."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.learning import AssessmentItem, AssessmentSession, Concept
from ...domain.services.learning_engine import LearningEngine
from ..ports.assessment import (
    AssessmentSessionPort,
    ConceptCatalogPort,
    ItemCatalogPort,
    LearnerPort,
    SessionIdPort,
)


@dataclass(frozen=True, slots=True)
class StartAssessmentCommand:
    """Input required to create a learner assessment session."""

    learner_id: str
    subject_id: str

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner id must not be empty")
        if not self.subject_id.strip():
            raise ValueError("subject id must not be empty")


@dataclass(frozen=True, slots=True)
class StartAssessmentResult:
    """Result returned after a session has been created."""

    session: AssessmentSession
    initial_concept: Concept
    initial_item: AssessmentItem


class StartAssessment:
    """Create a session and select its explainable baseline concept."""

    def __init__(
        self,
        *,
        learners: LearnerPort,
        concepts: ConceptCatalogPort,
        items: ItemCatalogPort,
        sessions: AssessmentSessionPort,
        session_ids: SessionIdPort,
    ) -> None:
        self._learners = learners
        self._concepts = concepts
        self._items = items
        self._sessions = sessions
        self._session_ids = session_ids

    def execute(self, command: StartAssessmentCommand) -> StartAssessmentResult:
        """Validate the request, select a baseline, and persist the session."""

        if not self._learners.exists(command.learner_id):
            raise ValueError(f"unknown learner: {command.learner_id}")
        if self._sessions.has_active_session(command.learner_id, command.subject_id):
            raise ValueError(
                "learner already has an active assessment for "
                f"subject: {command.subject_id}"
            )

        available_concepts = tuple(self._concepts.list_concepts(command.subject_id))
        if not available_concepts:
            raise ValueError(f"unknown subject or empty concept graph: {command.subject_id}")

        initial_concept = LearningEngine.select_initial_concept(available_concepts)
        available_items = tuple(self._items.list_items(command.subject_id))
        initial_item = LearningEngine.select_initial_item(initial_concept, available_items)
        session = AssessmentSession(
            id=self._session_ids.next_id(),
            learner_id=command.learner_id,
            subject_id=command.subject_id,
            current_concept_id=initial_concept.id,
        )
        self._sessions.create_session(session)
        return StartAssessmentResult(
            session=session,
            initial_concept=initial_concept,
            initial_item=initial_item,
        )
