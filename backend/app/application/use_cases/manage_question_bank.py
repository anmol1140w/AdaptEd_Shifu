"""Preview and import normalized teacher question-bank rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..ports.question_bank import QuestionBankIdPort, QuestionBankStorePort
from ...domain.entities.learning import Difficulty
from ...domain.entities.question_bank import BloomLevel, ClassifiedQuestion, QuestionDraft
from ...domain.services.question_classifier import QuestionClassifier


@dataclass(frozen=True, slots=True)
class QuestionBankPreview:
    rows: tuple[ClassifiedQuestion | None, ...]
    errors: tuple[tuple[str, ...], ...]

    @property
    def valid(self) -> bool:
        return bool(self.rows) and all(row is not None and not errors for row, errors in zip(self.rows, self.errors))


class ManageQuestionBank:
    def __init__(self, *, store: QuestionBankStorePort, ids: QuestionBankIdPort, classifier: QuestionClassifier | None = None) -> None:
        self._store = store
        self._ids = ids
        self._classifier = classifier or QuestionClassifier()

    def preview(self, records: Sequence[Mapping[str, object]]) -> QuestionBankPreview:
        if not records:
            raise ValueError("at least one question record is required")
        rows: list[ClassifiedQuestion | None] = []
        errors: list[tuple[str, ...]] = []
        for index, record in enumerate(records):
            try:
                draft = _draft(record)
                classification = self._classifier.classify(draft)
                suggested_bloom = classification.bloom_level
                suggested_difficulty = classification.difficulty
                final_bloom = draft.bloom_level or suggested_bloom
                final_difficulty = draft.difficulty or suggested_difficulty
                rows.append(ClassifiedQuestion(
                    question_id=f"preview-{index + 1}", draft=draft,
                    suggested_bloom_level=suggested_bloom,
                    bloom_confidence=classification.bloom_confidence,
                    bloom_reason=classification.bloom_reason,
                    bloom_source="teacher" if draft.bloom_level else "rule_based",
                    bloom_teacher_verified=draft.bloom_level is not None,
                    bloom_level=final_bloom,
                    suggested_difficulty=suggested_difficulty,
                    difficulty_source="teacher" if draft.difficulty else "rule_based",
                    difficulty_teacher_verified=draft.difficulty is not None,
                    difficulty=final_difficulty,
                ))
                errors.append(())
            except (TypeError, ValueError, KeyError) as exc:
                rows.append(None)
                errors.append((str(exc),))
        return QuestionBankPreview(tuple(rows), tuple(errors))

    def import_bank(self, *, teacher_id: str, title: str, records: Sequence[Mapping[str, object]]) -> tuple[str, tuple[ClassifiedQuestion, ...]]:
        if not teacher_id.strip() or not title.strip():
            raise ValueError("teacher_id and title must not be empty")
        preview = self.preview(records)
        if not preview.valid:
            raise ValueError("question bank contains invalid records; correct them before import")
        bank_id = self._ids.next_bank_id()
        imported = tuple(
            ClassifiedQuestion(
                question_id=self._ids.next_question_id(), draft=row.draft,
                suggested_bloom_level=row.suggested_bloom_level,
                bloom_confidence=row.bloom_confidence, bloom_reason=row.bloom_reason,
                bloom_source=row.bloom_source, bloom_teacher_verified=row.bloom_teacher_verified,
                bloom_level=row.bloom_level, suggested_difficulty=row.suggested_difficulty,
                difficulty_source=row.difficulty_source,
                difficulty_teacher_verified=row.difficulty_teacher_verified,
                difficulty=row.difficulty,
            )
            for row in preview.rows if row is not None
        )
        self._store.save_bank(bank_id=bank_id, teacher_id=teacher_id, title=title.strip(), questions=imported)
        return bank_id, imported


def _draft(record: Mapping[str, object]) -> QuestionDraft:
    if not isinstance(record, Mapping):
        raise TypeError("each question record must be an object")
    known = {"question", "question_type", "correct_answer", "difficulty", "bloom_level", "subject", "topic", "marks", "time_seconds", "explanation"}
    raw_fields: dict[str, Any] = {key: value for key, value in record.items() if key not in known}
    for key in ("question", "question_type", "subject", "topic"):
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
    difficulty = record.get("difficulty")
    bloom = record.get("bloom_level")
    if isinstance(bloom, str) and bloom.upper().startswith("BT"):
        bloom = bloom[2:]
    marks = record.get("marks")
    seconds = record.get("time_seconds")
    return QuestionDraft(
        question=str(record["question"]).strip(), question_type=str(record["question_type"]).strip().lower(),
        subject=str(record["subject"]).strip(), correct_answer=str(record.get("correct_answer") or "").strip(),
        topic=str(record["topic"]).strip(), fields=raw_fields,
        difficulty=None if difficulty in (None, "") else Difficulty(str(difficulty).lower()),
        bloom_level=None if bloom in (None, "") else BloomLevel(int(bloom)),
        marks=None if marks in (None, "") else float(marks),
        time_seconds=None if seconds in (None, "") else int(seconds),
        explanation=None if record.get("explanation") in (None, "") else str(record["explanation"]),
    )
