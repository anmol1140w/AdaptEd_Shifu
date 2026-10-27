"""Deterministic mastery calculation and next-action policy."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence

from ..entities.learning import (
    ActionType,
    AssessmentItem,
    AttemptEvidence,
    Concept,
    Difficulty,
    GapStatus,
    LearningOutcome,
    MasteryState,
    Recommendation,
    Trend,
)


class LearningEngine:
    """Evaluate evidence without depending on a database, API, or AI provider."""

    _RECENT_WINDOW = 5
    _CONFIDENT_EVIDENCE_COUNT = 4
    _TREND_DELTA = 0.15
    _DIFFICULTY_FACTORS = {
        Difficulty.EASY: 0.85,
        Difficulty.MEDIUM: 1.0,
        Difficulty.HARD: 1.1,
    }

    def __init__(self, concepts: Iterable[Concept]) -> None:
        concept_map = {concept.id: concept for concept in concepts}
        if not concept_map:
            raise ValueError("at least one concept is required")
        self._concepts = concept_map

    @staticmethod
    def select_initial_concept(concepts: Iterable[Concept]) -> Concept:
        """Select the deterministic baseline concept for a new assessment."""

        available = tuple(concepts)
        if not available:
            raise ValueError("at least one concept is required")

        roots = tuple(concept for concept in available if not concept.prerequisite_ids)
        return min(roots or available, key=lambda concept: concept.id)

    @staticmethod
    def select_initial_item(
        concept: Concept,
        items: Iterable[AssessmentItem],
    ) -> AssessmentItem:
        """Select the first approved item for a baseline concept."""

        candidates = tuple(
            item
            for item in items
            if item.approved
            and item.subject_id == concept.subject_id
            and item.concept_id == concept.id
        )
        if not candidates:
            raise ValueError(f"no approved assessment item for concept: {concept.id}")

        difficulty_order = {
            Difficulty.MEDIUM: 0,
            Difficulty.EASY: 1,
            Difficulty.HARD: 2,
        }
        return min(
            candidates,
            key=lambda item: (difficulty_order[item.difficulty], item.id),
        )

    def evaluate(
        self,
        *,
        focus_concept_id: str,
        attempts_by_concept: Mapping[str, Sequence[AttemptEvidence]],
        existing_states: Mapping[str, MasteryState] | None = None,
    ) -> LearningOutcome:
        """Return the updated state and next action for the focus concept.

        ``attempts_by_concept`` represents the evidence available at this point
        in the learning loop. The application layer can later load this mapping
        from a repository without changing the domain policy.
        """

        focus_concept = self._require_concept(focus_concept_id)
        normalized_attempts = self._validate_attempts(attempts_by_concept)
        focus_attempts = normalized_attempts.get(focus_concept.id, ())
        if not focus_attempts:
            raise ValueError("the focus concept must have at least one attempt")

        states = dict(existing_states or {})
        for concept_id, attempts in normalized_attempts.items():
            concept = self._require_concept(concept_id)
            states[concept_id] = self.calculate_mastery(concept, attempts)

        focus_state = states[focus_concept.id]
        blocker = self._find_blocker(focus_concept, states)
        gap_status = self._classify_gap(
            concept=focus_concept,
            state=focus_state,
            attempts=focus_attempts,
            has_blocker=blocker is not None,
        )
        recommendation = self._recommend(
            focus_concept=focus_concept,
            focus_state=focus_state,
            focus_attempts=focus_attempts,
            blocker=blocker,
            attempts_by_concept=normalized_attempts,
        )
        return LearningOutcome(
            mastery_state=focus_state,
            gap_status=gap_status,
            recommendation=recommendation,
        )

    @classmethod
    def calculate_mastery(
        cls,
        concept: Concept,
        attempts: Sequence[AttemptEvidence],
    ) -> MasteryState:
        """Calculate a transparent hybrid mastery state from recent evidence."""

        if not attempts:
            raise ValueError("at least one attempt is required")
        if any(attempt.concept_id != concept.id for attempt in attempts):
            raise ValueError("all attempts must belong to the supplied concept")

        recent = tuple(attempts[-cls._RECENT_WINDOW :])
        correctness = tuple(float(attempt.is_correct) for attempt in recent)
        recent_correctness = sum(correctness) / len(correctness)

        difficulty_adjusted = sum(
            float(attempt.is_correct) * cls._DIFFICULTY_FACTORS[attempt.difficulty]
            for attempt in recent
        ) / len(recent)

        if len(recent) > 1:
            retention = sum(correctness[1:]) / len(correctness[1:])
        else:
            retention = recent_correctness

        independence_score = sum(
            cls._independence_signal(attempt.hint_count) for attempt in recent
        ) / len(recent)
        response_confidence = sum(
            attempt.confidence_signal if attempt.confidence_signal is not None else 0.5
            for attempt in recent
        ) / len(recent)

        score = cls._clamp(
            0.50 * recent_correctness
            + 0.20 * difficulty_adjusted
            + 0.15 * retention
            + 0.10 * independence_score
            + 0.05 * response_confidence
        )
        confidence = min(1.0, len(attempts) / cls._CONFIDENT_EVIDENCE_COUNT)
        trend = cls._calculate_trend(recent)
        misconception = cls._most_common_misconception(recent)

        return MasteryState(
            concept_id=concept.id,
            score=round(score, 4),
            confidence=round(confidence, 4),
            evidence_count=len(attempts),
            trend=trend,
            likely_misconception=misconception,
            recent_correctness=round(recent_correctness, 4),
            independence_score=round(independence_score, 4),
        )

    @staticmethod
    def _validate_attempts(
        attempts_by_concept: Mapping[str, Sequence[AttemptEvidence]],
    ) -> dict[str, tuple[AttemptEvidence, ...]]:
        normalized: dict[str, tuple[AttemptEvidence, ...]] = {}
        for concept_id, attempts in attempts_by_concept.items():
            if not concept_id.strip():
                raise ValueError("attempt mapping contains an empty concept id")
            normalized_attempts = tuple(attempts)
            if any(attempt.concept_id != concept_id for attempt in normalized_attempts):
                raise ValueError("attempt mapping key does not match an attempt concept")
            normalized[concept_id] = normalized_attempts
        return normalized

    def _require_concept(self, concept_id: str) -> Concept:
        try:
            return self._concepts[concept_id]
        except KeyError as exc:
            raise ValueError(f"unknown concept: {concept_id}") from exc

    def _find_blocker(
        self,
        concept: Concept,
        states: Mapping[str, MasteryState],
    ) -> Concept | None:
        blockers: list[tuple[float, Concept]] = []
        for prerequisite_id in concept.prerequisite_ids:
            prerequisite = self._require_concept(prerequisite_id)
            state = states.get(prerequisite_id)
            if state is not None and state.evidence_count >= 2:
                if state.score < prerequisite.mastery_threshold:
                    blockers.append((state.score, prerequisite))
        if not blockers:
            return None
        return min(blockers, key=lambda item: item[0])[1]

    @classmethod
    def _classify_gap(
        cls,
        *,
        concept: Concept,
        state: MasteryState,
        attempts: Sequence[AttemptEvidence],
        has_blocker: bool,
    ) -> GapStatus:
        if has_blocker:
            return GapStatus.PREREQUISITE_BLOCKED
        if state.evidence_count < 2:
            return GapStatus.NOT_ENOUGH_EVIDENCE
        if state.score >= concept.mastery_threshold and state.confidence >= 0.75:
            if state.independence_score < 0.75 or cls._has_repeated_error(attempts):
                return GapStatus.FRAGILE
            return GapStatus.SECURE
        if state.score < 0.4 or cls._has_repeated_error(attempts):
            return GapStatus.NEEDS_SUPPORT
        return GapStatus.DEVELOPING

    @classmethod
    def _recommend(
        cls,
        *,
        focus_concept: Concept,
        focus_state: MasteryState,
        focus_attempts: Sequence[AttemptEvidence],
        blocker: Concept | None,
        attempts_by_concept: Mapping[str, Sequence[AttemptEvidence]],
    ) -> Recommendation:
        if blocker is not None:
            blocker_attempts = attempts_by_concept.get(blocker.id, ())
            evidence_ids = cls._evidence_ids(focus_attempts, blocker_attempts)
            repeated_error = cls._has_repeated_error(blocker_attempts)
            high_hint_use = cls._average_hint_count(blocker_attempts) >= 1.0
            reason = (
                f"{focus_concept.name} depends on {blocker.name}, but its mastery "
                "is below the prerequisite threshold."
            )
            return Recommendation(
                action_type=ActionType.PREREQUISITE_SUPPORT,
                target_concept_id=blocker.id,
                reason=reason,
                evidence_ids=evidence_ids,
                teacher_review_required=repeated_error and high_hint_use,
            )

        if focus_state.evidence_count < 2:
            return Recommendation(
                action_type=ActionType.BASELINE_CHECK,
                target_concept_id=focus_concept.id,
                reason=(
                    f"There is not enough evidence to estimate {focus_concept.name}; "
                    "collect another independent attempt."
                ),
                evidence_ids=cls._evidence_ids(focus_attempts),
            )

        if (
            focus_state.score >= focus_concept.mastery_threshold
            and focus_state.confidence >= 0.75
            and focus_state.independence_score >= 0.75
            and not cls._has_repeated_error(focus_attempts)
        ):
            return Recommendation(
                action_type=ActionType.TRANSFER_PRACTICE,
                target_concept_id=focus_concept.id,
                reason=(
                    f"{focus_concept.name} is secure with sufficient evidence and "
                    "low support use; test transfer with a harder or new-format item."
                ),
                evidence_ids=cls._evidence_ids(focus_attempts),
            )

        repeated_error = cls._has_repeated_error(focus_attempts)
        return Recommendation(
            action_type=ActionType.TARGETED_PRACTICE,
            target_concept_id=focus_concept.id,
            reason=(
                f"{focus_concept.name} is still developing; provide targeted practice "
                "and reassess before increasing difficulty."
            ),
            evidence_ids=cls._evidence_ids(focus_attempts),
            teacher_review_required=repeated_error and focus_state.confidence >= 0.5,
        )

    @classmethod
    def _calculate_trend(cls, attempts: Sequence[AttemptEvidence]) -> Trend:
        if len(attempts) < 2:
            return Trend.INSUFFICIENT_EVIDENCE
        midpoint = len(attempts) // 2
        earlier = sum(float(attempt.is_correct) for attempt in attempts[:midpoint]) / midpoint
        later_attempts = attempts[midpoint:]
        later = sum(float(attempt.is_correct) for attempt in later_attempts) / len(later_attempts)
        delta = later - earlier
        if delta >= cls._TREND_DELTA:
            return Trend.IMPROVING
        if delta <= -cls._TREND_DELTA:
            return Trend.DECLINING
        return Trend.STABLE

    @staticmethod
    def _most_common_misconception(
        attempts: Sequence[AttemptEvidence],
    ) -> str | None:
        labels = [attempt.misconception for attempt in attempts if attempt.misconception]
        if not labels:
            return None
        return Counter(labels).most_common(1)[0][0]

    @staticmethod
    def _independence_signal(hint_count: int) -> float:
        if hint_count == 0:
            return 1.0
        if hint_count == 1:
            return 0.65
        if hint_count == 2:
            return 0.4
        return 0.2

    @staticmethod
    def _average_hint_count(attempts: Sequence[AttemptEvidence]) -> float:
        if not attempts:
            return 0.0
        return sum(attempt.hint_count for attempt in attempts) / len(attempts)

    @staticmethod
    def _has_repeated_error(attempts: Sequence[AttemptEvidence]) -> bool:
        return len(attempts) >= 2 and not attempts[-1].is_correct and not attempts[-2].is_correct

    @staticmethod
    def _evidence_ids(*attempt_groups: Sequence[AttemptEvidence]) -> tuple[str, ...]:
        ids: list[str] = []
        for attempts in attempt_groups:
            for attempt in attempts[-5:]:
                if attempt.id not in ids:
                    ids.append(attempt.id)
        return tuple(ids)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))
