"""Persistence boundary for teacher-managed question banks."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ...domain.entities.question_bank import ClassifiedQuestion


class QuestionBankStorePort(Protocol):
    def save_bank(self, *, bank_id: str, teacher_id: str, title: str, questions: Sequence[ClassifiedQuestion]) -> None:
        """Persist a validated bank and its questions atomically where supported."""
        ...


class QuestionBankIdPort(Protocol):
    def next_bank_id(self) -> str: ...

    def next_question_id(self) -> str: ...
