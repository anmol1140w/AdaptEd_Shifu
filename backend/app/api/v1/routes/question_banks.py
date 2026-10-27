"""Teacher-only v1 question-bank preview and import adapter."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ....application.question_bank_facade import QuestionBankFacade
from ....schemas.question_bank_v1 import QuestionBankContractError
from .assessment import AssessmentApiResponse
from .teacher_interventions import TeacherRequestContext


@dataclass(frozen=True, slots=True)
class QuestionBankApi:
    facade: QuestionBankFacade

    PREVIEW_PATH = "/api/v1/teacher/question-banks/preview"
    IMPORT_PATH = "/api/v1/teacher/question-banks"

    def preview(self, payload: Mapping[str, object], *, context: TeacherRequestContext | None) -> AssessmentApiResponse:
        denied = self._authorize(context)
        if denied:
            return denied
        try:
            return AssessmentApiResponse(200, self.facade.preview(payload))
        except (QuestionBankContractError, ValueError) as exc:
            return self._error(400, "invalid_question_bank", str(exc))

    def import_bank(self, payload: Mapping[str, object], *, context: TeacherRequestContext | None) -> AssessmentApiResponse:
        denied = self._authorize(context)
        if denied:
            return denied
        try:
            return AssessmentApiResponse(201, self.facade.import_bank(payload, teacher_id=context.principal_id))
        except QuestionBankContractError as exc:
            return self._error(400, "invalid_question_bank", str(exc))
        except ValueError as exc:
            return self._error(422, "question_bank_rejected", str(exc))

    @staticmethod
    def _authorize(context: TeacherRequestContext | None) -> AssessmentApiResponse | None:
        if context is None:
            return QuestionBankApi._error(401, "authentication_required", "Teacher authentication is required.")
        if context.role != "teacher":
            return QuestionBankApi._error(403, "teacher_role_required", "A teacher role is required.")
        return None

    @staticmethod
    def _error(status: int, code: str, message: str) -> AssessmentApiResponse:
        return AssessmentApiResponse(status, {"error": {"code": code, "message": message}})
