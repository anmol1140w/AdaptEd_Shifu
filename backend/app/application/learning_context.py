"""Load persisted learner evidence for support and scaffold decisions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .ports.learning import AttemptPort, MasteryStatePort
from ..domain.entities.learning import (
    AttemptEvidence,
    Concept,
    GapStatus,
    MasteryState,
    Recommendation,
)
from ..domain.services.learning_engine import LearningEngine


@dataclass(frozen=True, slots=True)
class LearnerConceptContext:
    """Traceable evidence and policy context for one learner/concept pair."""

    evidence: tuple[AttemptEvidence, ...] = ()
    mastery_state: MasteryState | None = None
    gap_status: GapStatus | None = None
    recommendation: Recommendation | None = None
    misconception: str | None = None

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(attempt.id for attempt in self.evidence)


def load_learner_concept_context(
    *,
    learner_id: str,
    concept: Concept,
    concepts: Sequence[Concept],
    attempts: AttemptPort | None,
    mastery_states: MasteryStatePort | None,
) -> LearnerConceptContext:
    """Read evidence through ports and recalculate a current policy snapshot."""

    if attempts is None:
        return LearnerConceptContext()
    history = attempts.list_attempts(learner_id)
    concept_ids = {candidate.id for candidate in concepts}
    attempts_by_concept = {
        concept_id: tuple(concept_attempts)
        for concept_id, concept_attempts in history.items()
        if concept_id in concept_ids and concept_attempts
    }
    evidence = tuple(attempts_by_concept.get(concept.id, ()))
    states = dict(mastery_states.get_states(learner_id)) if mastery_states is not None else {}
    stored_state = states.get(concept.id)
    if not evidence:
        return LearnerConceptContext(
            mastery_state=stored_state,
            misconception=stored_state.likely_misconception if stored_state else None,
        )

    engine = LearningEngine(concepts)
    outcome = engine.evaluate(
        focus_concept_id=concept.id,
        attempts_by_concept=attempts_by_concept,
        existing_states=states,
    )
    misconception = next(
        (attempt.misconception for attempt in reversed(evidence) if attempt.misconception),
        outcome.mastery_state.likely_misconception,
    )
    return LearnerConceptContext(
        evidence=evidence,
        mastery_state=outcome.mastery_state,
        gap_status=outcome.gap_status,
        recommendation=outcome.recommendation,
        misconception=misconception,
    )
