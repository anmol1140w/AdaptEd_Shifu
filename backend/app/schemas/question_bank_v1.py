"""V1 request and response mapping for question-bank preview and import."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..application.use_cases.manage_question_bank import ManageQuestionBank, QuestionBankPreview
from ..domain.entities.question_bank import ClassifiedQuestion


class QuestionBankContractError(ValueError):
    pass


def parse_question_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    if not isinstance(payload, Mapping) or payload.get("contract_version") != "v1":
        raise QuestionBankContractError("contract_version must be 'v1'")
    if set(payload) - {"contract_version", "records"} or "records" not in payload:
        raise QuestionBankContractError("payload must contain only contract_version and records")
    records = payload["records"]
    if not isinstance(records, list) or not all(isinstance(row, Mapping) for row in records):
        raise QuestionBankContractError("records must be an array of objects")
    return records  # type: ignore[return-value]


def preview_payload(preview: QuestionBankPreview) -> dict[str, Any]:
    return {"contract_version": "v1", "valid": preview.valid,
            "questions": [None if row is None else question_payload(row) for row in preview.rows],
            "errors": [{"row": index + 1, "messages": list(errors)} for index, errors in enumerate(preview.errors) if errors]}


def imported_payload(bank_id: str, title: str, questions: tuple[ClassifiedQuestion, ...]) -> dict[str, Any]:
    return {"contract_version": "v1", "question_bank": {"id": bank_id, "title": title, "question_count": len(questions)},
            "questions": [question_payload(question) for question in questions]}


def question_payload(question: ClassifiedQuestion) -> dict[str, Any]:
    draft = question.draft
    return {"id": question.question_id, "question": draft.question, "question_type": draft.question_type,
            "correct_answer": draft.correct_answer, "subject": draft.subject, "topic": draft.topic,
            "fields": dict(draft.fields), "marks": draft.marks, "time_seconds": draft.time_seconds,
            "explanation": draft.explanation,
            "bloom": {"level": question.bloom_level.code, "suggested_level": question.suggested_bloom_level.code,
                      "source": question.bloom_source, "confidence": question.bloom_confidence,
                      "reason": question.bloom_reason, "teacher_verified": question.bloom_teacher_verified},
            "difficulty": {"level": question.difficulty.value, "suggested_level": question.suggested_difficulty.value,
                           "source": question.difficulty_source, "teacher_verified": question.difficulty_teacher_verified}}


def run_preview(payload: Mapping[str, object], manager: ManageQuestionBank) -> dict[str, Any]:
    try:
        rows = parse_question_rows(payload)
        return preview_payload(manager.preview(rows))
    except (TypeError, ValueError) as exc:
        raise QuestionBankContractError(str(exc)) from exc
