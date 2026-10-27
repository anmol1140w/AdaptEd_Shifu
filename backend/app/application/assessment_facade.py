"""Framework-independent orchestration for the v1 assessment transport flow."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..schemas.assessment_v1 import (
    parse_start_assessment_request,
    parse_submit_attempt_request,
    parse_subject_summary_request,
    start_assessment_response,
    subject_summary_response,
    submit_attempt_response,
)
from ..domain.entities.learning import AttemptEvidence, Concept
from .ports.assessment import ConceptCatalogPort, ItemCatalogPort
from .ports.learning import AttemptPort
from .use_cases.build_subject_summary import BuildSubjectSummary
from .use_cases.prepare_attempt import PrepareAttempt
from .use_cases.start_assessment import StartAssessment
from .use_cases.submit_attempt import SubmitAttempt, SubmitAttemptCommand


class AssessmentFacadeError(ValueError):
    """Raised when the facade cannot enrich an application result for v1."""


class AssessmentFacade:
    """Coordinate transport parsing, grading, learning and response mapping."""

    def __init__(
        self,
        *,
        start_assessment: StartAssessment,
        prepare_attempt: PrepareAttempt,
        submit_attempt: SubmitAttempt,
        concepts: ConceptCatalogPort,
        items: ItemCatalogPort,
        attempts: AttemptPort,
        subject_names: Mapping[str, str],
        build_subject_summary: BuildSubjectSummary | None = None,
    ) -> None:
        self._start_assessment = start_assessment
        self._prepare_attempt = prepare_attempt
        self._submit_attempt = submit_attempt
        self._concepts = concepts
        self._items = items
        self._attempts = attempts
        self._subject_names = dict(subject_names)
        self._build_subject_summary = build_subject_summary

    def start(self, payload: Mapping[str, object]) -> dict[str, Any]:
        """Run the start-assessment flow and return the v1 response payload."""

        command = parse_start_assessment_request(payload)
        result = self._start_assessment.execute(command)
        return start_assessment_response(
            result,
            subject_name=self._subject_name(result.session.subject_id),
        )

    def submit(self, payload: Mapping[str, object]) -> dict[str, Any]:
        """Run parse, grade, learning evaluation and response mapping in order."""

        request = parse_submit_attempt_request(payload)
        evidence = self._prepare_attempt.execute(request)
        result = self._submit_attempt.execute(
            SubmitAttemptCommand(
                session_id=request.session_id,
                learner_id=request.learner_id,
                attempt=evidence,
            )
        )
        concept = self._concept_for(
            subject_id=result.session.subject_id,
            concept_id=result.attempt.concept_id,
        )
        item = self._items.get_item(result.attempt.item_id)
        if item is None:
            raise AssessmentFacadeError(
                f"assessment item disappeared after evaluation: {result.attempt.item_id}"
            )
        return submit_attempt_response(
            result,
            subject_name=self._subject_name(result.session.subject_id),
            concept=concept,
            item=item,
            evidence_references=self._evidence_references(
                learner_id=result.learner_id,
                current=evidence,
            ),
        )

    def summary(self, payload: Mapping[str, object]) -> dict[str, Any]:
        """Build a subject summary without coupling it to an HTTP framework."""

        if self._build_subject_summary is None:
            raise AssessmentFacadeError("subject summary use case is not configured")
        command = parse_subject_summary_request(payload)
        result = self._build_subject_summary.execute(command)
        return subject_summary_response(
            result,
            subject_name=self._subject_name(result.subject_id),
        )

    def _subject_name(self, subject_id: str) -> str:
        try:
            subject_name = self._subject_names[subject_id]
        except KeyError as exc:
            raise AssessmentFacadeError(f"unknown subject name: {subject_id}") from exc
        if not subject_name.strip():
            raise AssessmentFacadeError(f"subject name is empty: {subject_id}")
        return subject_name

    def _concept_for(self, *, subject_id: str, concept_id: str) -> Concept:
        concept = next(
            (
                candidate
                for candidate in self._concepts.list_concepts(subject_id)
                if candidate.id == concept_id
            ),
            None,
        )
        if concept is None:
            raise AssessmentFacadeError(f"unknown response concept: {concept_id}")
        return concept

    def _evidence_references(
        self,
        *,
        learner_id: str,
        current: AttemptEvidence,
    ) -> tuple[AttemptEvidence, ...]:
        references: list[AttemptEvidence] = []
        seen_ids: set[str] = set()
        for concept_attempts in self._attempts.list_attempts(learner_id).values():
            for attempt in concept_attempts:
                if attempt.id not in seen_ids:
                    references.append(attempt)
                    seen_ids.add(attempt.id)
        if current.id not in seen_ids:
            references.append(current)
        return tuple(references)
