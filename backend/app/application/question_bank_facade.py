"""Framework-independent question-bank workflow boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..schemas.question_bank_v1 import imported_payload, parse_question_rows, preview_payload
from .use_cases.manage_question_bank import ManageQuestionBank


class QuestionBankFacade:
    def __init__(self, *, manager: ManageQuestionBank) -> None:
        self._manager = manager

    def preview(self, payload: Mapping[str, object]) -> dict[str, Any]:
        rows = parse_question_rows(payload)
        return preview_payload(self._manager.preview(rows))

    def import_bank(self, payload: Mapping[str, object], *, teacher_id: str) -> dict[str, Any]:
        if not isinstance(payload, Mapping) or payload.get("contract_version") != "v1":
            raise ValueError("contract_version must be 'v1'")
        if set(payload) != {"contract_version", "title", "records"}:
            raise ValueError("payload must contain contract_version, title, and records")
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        rows = parse_question_rows({"contract_version": "v1", "records": payload.get("records")})
        bank_id, questions = self._manager.import_bank(teacher_id=teacher_id, title=title, records=rows)
        return imported_payload(bank_id, title.strip(), questions)
