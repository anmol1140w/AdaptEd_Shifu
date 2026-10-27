"""Run the synthetic Riya and Arjun assessment flow from the repository root."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
import sys
from typing import Any


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.api.v1.routes.assessment import LearnerRequestContext
from backend.app.api.v1.routes.teacher_interventions import TeacherRequestContext
from backend.app.application.ports.ai import RetrievedSource
from backend.app.bootstrap import InMemoryAssessmentRuntime, build_in_memory_assessment_runtime
from backend.app.domain.entities.learning import AssessmentItem, Concept, Difficulty


SUBJECT_ID = "maths-9"
SUBJECT_NAME = "Class 9 Mathematics"
CONCEPT_ID = "ALG-EQ-02"


def build_demo_runtime() -> InMemoryAssessmentRuntime:
    """Build the synthetic runtime used by the local demo."""

    concept = Concept(
        id=CONCEPT_ID,
        subject_id=SUBJECT_ID,
        name="Two-step equations",
    )
    medium_item = AssessmentItem(
        id="demo-item-medium",
        subject_id=SUBJECT_ID,
        concept_id=CONCEPT_ID,
        difficulty=Difficulty.MEDIUM,
        question="Solve x + 3 = 7.",
        answer="x = 4",
        misconception_tag="did not isolate the constant",
    )
    hard_item = AssessmentItem(
        id="demo-item-hard",
        subject_id=SUBJECT_ID,
        concept_id=CONCEPT_ID,
        difficulty=Difficulty.HARD,
        question="Solve 3(x - 2) + 5 = 41.",
        answer="x = 14",
    )
    return build_in_memory_assessment_runtime(
        learner_ids=("learner-riya", "learner-arjun"),
        concepts=(concept,),
        items=(
            medium_item,
            AssessmentItem(
                id="demo-item-medium-2",
                subject_id=SUBJECT_ID,
                concept_id=CONCEPT_ID,
                difficulty=Difficulty.MEDIUM,
                question="Solve x + 4 = 9.",
                answer="x = 5",
            ),
            AssessmentItem(
                id="demo-item-easy",
                subject_id=SUBJECT_ID,
                concept_id=CONCEPT_ID,
                difficulty=Difficulty.EASY,
                question="Solve x + 1 = 2.",
                answer="x = 1",
            ),
            hard_item,
            AssessmentItem(
                id="demo-item-hard-2",
                subject_id=SUBJECT_ID,
                concept_id=CONCEPT_ID,
                difficulty=Difficulty.HARD,
                question="Solve 4(x + 1) - 3 = 25.",
                answer="x = 6",
            ),
        ),
        subject_names={SUBJECT_ID: SUBJECT_NAME},
        session_id_prefix="demo-session",
        use_grok=True,
        sources=(
            RetrievedSource(
                source_id="demo-lesson-equations-01",
                subject_id=SUBJECT_ID,
                concept_id=CONCEPT_ID,
                title="Two-step equations lesson",
                text="Undo addition before division and check each operation.",
                confidence=0.95,
            ),
        ),
    )


def run_demo() -> dict[str, Any]:
    """Run both synthetic learner paths and return JSON-serializable results."""

    runtime = build_demo_runtime()
    riya_context = LearnerRequestContext(principal_id="learner-riya")
    arjun_context = LearnerRequestContext(principal_id="learner-arjun")

    riya_start = _start(runtime, "learner-riya", riya_context)
    arjun_start = _start(runtime, "learner-arjun", arjun_context)
    riya_session_id = riya_start["session"]["id"]
    arjun_session_id = arjun_start["session"]["id"]

    riya_first = _submit(
            runtime,
            learner_id="learner-riya",
            session_id=riya_session_id,
            context=riya_context,
            attempt_id="demo-riya-1",
            item_id="demo-item-medium",
            answer="x = 5",
            hint_count=2,
        )
    riya_submissions = [riya_first, _submit(
            runtime,
            learner_id="learner-riya",
            session_id=riya_session_id,
            context=riya_context,
            attempt_id="demo-riya-2",
            item_id=_next_item_id(riya_first, "demo-item-medium-2"),
            answer="x = 6",
            hint_count=2,
        )]
    arjun_first = _submit(
            runtime,
            learner_id="learner-arjun",
            session_id=arjun_session_id,
            context=arjun_context,
            attempt_id="demo-arjun-1",
            item_id="demo-item-medium",
            answer="x = 4",
        )
    arjun_second = _submit(
            runtime,
            learner_id="learner-arjun",
            session_id=arjun_session_id,
            context=arjun_context,
            attempt_id="demo-arjun-2",
            item_id=_next_item_id(arjun_first, "demo-item-medium-2"),
            answer="x = 5",
        )
    arjun_third = _submit(
            runtime,
            learner_id="learner-arjun",
            session_id=arjun_session_id,
            context=arjun_context,
            attempt_id="demo-arjun-3",
            item_id=_next_item_id(arjun_second, "demo-item-easy"),
            answer="x = 1",
        )
    arjun_submissions = [arjun_first, arjun_second, arjun_third, _submit(
            runtime,
            learner_id="learner-arjun",
            session_id=arjun_session_id,
            context=arjun_context,
            attempt_id="demo-arjun-4",
            item_id=_next_item_id(arjun_third, "demo-item-hard"),
            answer="x = 14",
        )]

    tutor = runtime.support_api.tutor(
        {
            "contract_version": "v1",
            "learner_id": "learner-riya",
            "subject_id": SUBJECT_ID,
            "concept_id": CONCEPT_ID,
            "mode": "hint",
            "learner_answer": "x = 6",
        },
        context=riya_context,
    )
    quiz = runtime.support_api.weak_area_quiz(
        {
            "contract_version": "v1",
            "learner_id": "learner-riya",
            "subject_id": SUBJECT_ID,
            "concept_id": CONCEPT_ID,
            "difficulty": "hard",
            "item_count": 2,
        },
        context=riya_context,
    )
    teacher_queue = runtime.intervention_api.queue(
        {"contract_version": "v1", "subject_id": SUBJECT_ID},
        context=TeacherRequestContext(
            principal_id="teacher-demo",
            allowed_learner_ids=("learner-riya", "learner-arjun"),
        ),
    )

    return {
        "demo": {
            "synthetic": True,
            "subject_id": SUBJECT_ID,
            "subject_name": SUBJECT_NAME,
            "note": "Synthetic local run; not classroom evidence.",
        },
        "learners": {
            "riya": {
                "start": riya_start,
                "submissions": riya_submissions,
                "persisted_attempt_count": _attempt_count(runtime, "learner-riya"),
                "latest_recommendation": _recommendation_payload(
                    runtime.recommendations.latest("learner-riya")
                ),
            },
            "arjun": {
                "start": arjun_start,
                "submissions": arjun_submissions,
                "persisted_attempt_count": _attempt_count(runtime, "learner-arjun"),
                "latest_recommendation": _recommendation_payload(
                    runtime.recommendations.latest("learner-arjun")
                ),
            },
        },
        "support": {
            "tutor": tutor.body,
            "quiz": quiz.body,
        },
        "teacher_interventions": teacher_queue.body,
    }


def main() -> None:
    """Print the synthetic demo result as formatted JSON."""

    print(json.dumps(run_demo(), indent=2, sort_keys=True, default=_json_default))


def _start(
    runtime: InMemoryAssessmentRuntime,
    learner_id: str,
    context: LearnerRequestContext,
) -> dict[str, Any]:
    response = runtime.api.start(
        {
            "contract_version": "v1",
            "learner_id": learner_id,
            "subject_id": SUBJECT_ID,
        },
        context=context,
    )
    if response.status_code != 201:
        raise RuntimeError(f"demo start failed for {learner_id}: {response.body}")
    if "answer" in response.body["item"]:
        raise RuntimeError("demo response exposed an assessment-item answer")
    return response.body


def _submit(
    runtime: InMemoryAssessmentRuntime,
    *,
    learner_id: str,
    session_id: str,
    context: LearnerRequestContext,
    attempt_id: str,
    item_id: str,
    answer: str,
    hint_count: int = 0,
) -> dict[str, Any]:
    response = runtime.api.submit(
        {
            "contract_version": "v1",
            "session_id": session_id,
            "learner_id": learner_id,
            "attempt": {
                "id": attempt_id,
                "item_id": item_id,
                "concept_id": CONCEPT_ID,
                "answer": answer,
                "response_ms": 1000,
                "hint_count": hint_count,
            },
        },
        context=context,
    )
    if response.status_code != 200:
        raise RuntimeError(f"demo submit failed for {learner_id}: {response.body}")
    if "answer" in response.body["item"]:
        raise RuntimeError("demo response exposed an assessment-item answer")
    return response.body


def _attempt_count(runtime: InMemoryAssessmentRuntime, learner_id: str) -> int:
    return sum(
        len(attempts)
        for attempts in runtime.attempts.list_attempts(learner_id).values()
    )


def _next_item_id(response: dict[str, Any], fallback: str) -> str:
    next_item = response.get("next_item")
    if isinstance(next_item, dict) and isinstance(next_item.get("id"), str):
        return next_item["id"]
    return fallback


def _recommendation_payload(recommendation: object) -> dict[str, Any] | None:
    if recommendation is None:
        return None
    return {
        "action_type": recommendation.action_type.value,
        "target_concept_id": recommendation.target_concept_id,
        "reason": recommendation.reason,
        "evidence_reference_ids": list(recommendation.evidence_ids),
        "teacher_review_required": recommendation.teacher_review_required,
    }


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"value is not JSON serializable: {type(value).__name__}")


if __name__ == "__main__":
    main()
