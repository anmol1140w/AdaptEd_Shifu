"""Behavior tests for the backend assessment contract v1 mapper."""

from __future__ import annotations

import json
import unittest

from backend.app.application.use_cases.build_subject_summary import (
    BuildSubjectSummaryCommand,
    ConceptSummary,
    SubjectSummary,
)
from backend.app.application.use_cases.start_assessment import StartAssessmentResult
from backend.app.application.use_cases.submit_attempt import SubmitAttemptResult
from backend.app.domain.entities.learning import (
    ActionType,
    AssessmentItem,
    AssessmentSession,
    AttemptEvidence,
    Concept,
    Difficulty,
    GapStatus,
    LearningOutcome,
    Recommendation,
)
from backend.app.domain.services.learning_engine import LearningEngine
from backend.app.schemas.assessment_v1 import (
    AssessmentContractError,
    parse_start_assessment_request,
    parse_submit_attempt_request,
    parse_subject_summary_request,
    start_assessment_response,
    subject_summary_response,
    submit_attempt_response,
    to_attempt_evidence,
)


class AssessmentV1SchemaTests(unittest.TestCase):
    def test_start_request_maps_to_application_command(self) -> None:
        command = parse_start_assessment_request(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
            }
        )

        self.assertEqual(command.learner_id, "learner-riya")
        self.assertEqual(command.subject_id, "maths-9")

    def test_start_request_rejects_unknown_fields_and_wrong_version(self) -> None:
        with self.assertRaisesRegex(AssessmentContractError, "unexpected fields"):
            parse_start_assessment_request(
                {
                    "contract_version": "v1",
                    "learner_id": "learner-riya",
                    "subject_id": "maths-9",
                    "extra": "not-supported",
                }
            )

        with self.assertRaisesRegex(AssessmentContractError, "contract_version"):
            parse_start_assessment_request(
                {
                    "contract_version": "v2",
                    "learner_id": "learner-riya",
                    "subject_id": "maths-9",
                }
            )

    def test_subject_summary_request_maps_to_application_command(self) -> None:
        command = parse_subject_summary_request(
            {
                "contract_version": "v1",
                "learner_id": "learner-riya",
                "subject_id": "maths-9",
            }
        )

        self.assertIsInstance(command, BuildSubjectSummaryCommand)
        self.assertEqual(command.learner_id, "learner-riya")
        self.assertEqual(command.subject_id, "maths-9")

    def test_submit_request_accepts_optional_interaction_fields(self) -> None:
        request = parse_submit_attempt_request(
            {
                "contract_version": "v1",
                "session_id": "session-riya",
                "learner_id": "learner-riya",
                "attempt": {
                    "id": "attempt-1",
                    "item_id": "item-1",
                    "concept_id": "ALG-EQ-02",
                    "answer": "x = 4",
                    "hint_count": 1,
                },
            }
        )

        self.assertEqual(request.answer, "x = 4")
        self.assertEqual(request.hint_count, 1)
        self.assertIsNone(request.response_ms)
        self.assertIsNone(request.confidence_signal)

    def test_submit_request_rejects_invalid_interaction_values(self) -> None:
        base_payload = {
            "contract_version": "v1",
            "session_id": "session-riya",
            "learner_id": "learner-riya",
            "attempt": {
                "id": "attempt-1",
                "item_id": "item-1",
                "concept_id": "ALG-EQ-02",
                "answer": "x = 4",
                "hint_count": 1,
            },
        }

        negative_hints = {**base_payload, "attempt": {**base_payload["attempt"], "hint_count": -1}}
        with self.assertRaisesRegex(AssessmentContractError, "hint_count"):
            parse_submit_attempt_request(negative_hints)

        wrong_answer_field = {
            **base_payload,
            "attempt": {**base_payload["attempt"], "is_correct": True},
        }
        with self.assertRaisesRegex(AssessmentContractError, "unexpected fields"):
            parse_submit_attempt_request(wrong_answer_field)

    def test_grading_boundary_converts_raw_request_to_domain_evidence(self) -> None:
        request = parse_submit_attempt_request(
            {
                "contract_version": "v1",
                "session_id": "session-riya",
                "learner_id": "learner-riya",
                "attempt": {
                    "id": "attempt-1",
                    "item_id": "item-1",
                    "concept_id": "ALG-EQ-02",
                    "answer": "x = 5",
                    "response_ms": 1200,
                    "hint_count": 2,
                    "confidence_signal": 0.4,
                },
            }
        )

        evidence = to_attempt_evidence(
            request,
            is_correct=False,
            difficulty="medium",
            misconception="subtracted before dividing",
        )

        self.assertEqual(evidence.id, "attempt-1")
        self.assertFalse(evidence.is_correct)
        self.assertEqual(evidence.difficulty, Difficulty.MEDIUM)
        self.assertEqual(evidence.response_ms, 1200)
        self.assertEqual(evidence.misconception, "subtracted before dividing")
        self.assertFalse(hasattr(evidence, "answer"))

    def test_start_response_is_json_safe_and_redacts_item_answer(self) -> None:
        concept = Concept(
            id="ALG-VAR-01",
            subject_id="maths-9",
            name="Variables and expressions",
        )
        item = AssessmentItem(
            id="item-var-1",
            subject_id="maths-9",
            concept_id=concept.id,
            difficulty=Difficulty.MEDIUM,
            question="Simplify 3x + 2x.",
            answer="5x",
            source_id="lesson-variables-01",
        )
        result = StartAssessmentResult(
            session=AssessmentSession(
                id="session-1",
                learner_id="learner-riya",
                subject_id="maths-9",
                current_concept_id=concept.id,
            ),
            initial_concept=concept,
            initial_item=item,
        )

        response = start_assessment_response(result, subject_name="Class 9 Mathematics")
        encoded = json.dumps(response)

        self.assertEqual(json.loads(encoded), response)
        self.assertEqual(response["contract_version"], "v1")
        self.assertEqual(response["item"]["id"], item.id)
        self.assertNotIn("answer", response["item"])

    def test_subject_summary_response_preserves_unassessed_concept_drilldown(self) -> None:
        concept = Concept(
            id="ALG-VAR-01",
            subject_id="maths-9",
            name="Variables and expressions",
        )
        result = SubjectSummary(
            learner_id="learner-riya",
            subject_id="maths-9",
            concepts=(
                ConceptSummary(
                    concept=concept,
                    mastery_state=None,
                    gap_status=GapStatus.NOT_ENOUGH_EVIDENCE,
                    recommendation=None,
                ),
            ),
            mastery_score=0.0,
            confidence=0.0,
            evidence_count=0,
            gap_status_counts=((GapStatus.NOT_ENOUGH_EVIDENCE, 1),),
        )

        response = subject_summary_response(result, subject_name="Class 9 Mathematics")

        self.assertEqual(json.loads(json.dumps(response)), response)
        self.assertEqual(response["summary"]["concept_count"], 1)
        self.assertEqual(response["summary"]["assessed_concept_count"], 0)
        self.assertEqual(response["concepts"][0]["concept"]["id"], concept.id)
        self.assertIsNone(response["concepts"][0]["mastery"])
        self.assertEqual(
            response["concepts"][0]["gap_status"],
            "not_enough_evidence",
        )

    def test_submit_response_maps_mastery_and_recommendation_references(self) -> None:
        concept = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
        )
        attempts = tuple(
            AttemptEvidence(
                id=f"eq-{index}",
                item_id=f"item-eq-{index}",
                concept_id=concept.id,
                is_correct=True,
                difficulty=Difficulty.HARD if index >= 3 else Difficulty.MEDIUM,
                hint_count=0,
                confidence_signal=0.9,
            )
            for index in range(1, 5)
        )
        current_attempt = attempts[-1]
        state = LearningEngine.calculate_mastery(concept, attempts)
        recommendation = Recommendation(
            action_type=ActionType.TRANSFER_PRACTICE,
            target_concept_id=concept.id,
            reason="Secure mastery supports transfer practice.",
            evidence_ids=tuple(attempt.id for attempt in attempts),
        )
        result = SubmitAttemptResult(
            session=AssessmentSession(
                id="session-arjun",
                learner_id="learner-arjun",
                subject_id="maths-9",
                current_concept_id=concept.id,
            ),
            learner_id="learner-arjun",
            attempt=current_attempt,
            outcome=LearningOutcome(
                mastery_state=state,
                gap_status=GapStatus.SECURE,
                recommendation=recommendation,
            ),
        )
        item = AssessmentItem(
            id=current_attempt.item_id,
            subject_id="maths-9",
            concept_id=concept.id,
            difficulty=current_attempt.difficulty,
            question="Solve 3(x - 2) + 5 = 41.",
            answer="x = 14",
        )

        response = submit_attempt_response(
            result,
            subject_name="Class 9 Mathematics",
            concept=concept,
            item=item,
            evidence_references=attempts,
        )

        self.assertEqual(json.loads(json.dumps(response)), response)
        self.assertEqual(response["mastery"]["concept_id"], concept.id)
        self.assertEqual(response["recommendation"]["action_type"], "transfer_practice")
        self.assertEqual(
            response["recommendation"]["evidence_reference_ids"],
            ["eq-1", "eq-2", "eq-3", "eq-4"],
        )
        self.assertEqual(response["session"]["current_concept_id"], concept.id)

    def test_submit_response_rejects_incomplete_recommendation_references(self) -> None:
        concept = Concept(
            id="ALG-EQ-02",
            subject_id="maths-9",
            name="Two-step equations",
        )
        attempt = AttemptEvidence(
            id="eq-2",
            item_id="item-eq-2",
            concept_id=concept.id,
            is_correct=True,
            difficulty=Difficulty.MEDIUM,
        )
        result = SubmitAttemptResult(
            session=AssessmentSession(
                id="session-1",
                learner_id="learner-arjun",
                subject_id="maths-9",
                current_concept_id=concept.id,
            ),
            learner_id="learner-arjun",
            attempt=attempt,
            outcome=LearningOutcome(
                mastery_state=LearningEngine.calculate_mastery(concept, [attempt]),
                gap_status=GapStatus.NOT_ENOUGH_EVIDENCE,
                recommendation=Recommendation(
                    action_type=ActionType.BASELINE_CHECK,
                    target_concept_id=concept.id,
                    reason="Collect another attempt.",
                    evidence_ids=(attempt.id, "missing-reference"),
                ),
            ),
        )
        item = AssessmentItem(
            id=attempt.item_id,
            subject_id="maths-9",
            concept_id=concept.id,
            difficulty=Difficulty.MEDIUM,
            question="Solve x + 3 = 7.",
            answer="x = 4",
        )

        with self.assertRaisesRegex(AssessmentContractError, "missing-reference"):
            submit_attempt_response(
                result,
                subject_name="Class 9 Mathematics",
                concept=concept,
                item=item,
                evidence_references=(attempt,),
            )


if __name__ == "__main__":
    unittest.main()
