"""Inspectable, rule-based question metadata suggestions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..entities.learning import Difficulty
from ..entities.question_bank import BloomLevel, QuestionDraft


@dataclass(frozen=True, slots=True)
class QuestionClassification:
    bloom_level: BloomLevel
    bloom_confidence: float
    bloom_reason: str
    difficulty: Difficulty
    difficulty_reason: str


class QuestionClassifier:
    """Suggest Bloom level and difficulty independently; never calls an AI API."""

    _PATTERNS: tuple[tuple[BloomLevel, tuple[str, ...]], ...] = (
        (BloomLevel.CREATE, ("design", "create", "construct", "develop", "formulate", "propose")),
        (BloomLevel.EVALUATE, ("evaluate", "justify", "defend", "critique", "assess", "rank")),
        (BloomLevel.ANALYZE, ("analyze", "analyse", "compare", "contrast", "differentiate", "infer", "debug", "identify the error")),
        (BloomLevel.APPLY, ("calculate", "solve", "apply", "use", "compute", "determine", "find", "implement")),
        (BloomLevel.UNDERSTAND, ("explain", "summarize", "interpret", "describe", "classify", "illustrate", "why")),
        (BloomLevel.REMEMBER, ("define", "state", "list", "name", "recall", "identify", "what is", "when was")),
    )

    def classify(self, question: QuestionDraft) -> QuestionClassification:
        text = f"{question.question} {question.topic}".casefold()
        words = re.sub(r"[^a-z0-9]+", " ", text)
        matched: list[tuple[BloomLevel, str]] = []
        for level, phrases in self._PATTERNS:
            for phrase in phrases:
                if re.search(rf"\b{re.escape(phrase)}\b", words):
                    matched.append((level, phrase))
                    break
        if matched:
            level, phrase = matched[0]
            confidence = 0.76 if len(matched) == 1 else 0.62
            reason = f"Action verb '{phrase}' matched the {level.name.lower()} rule."
        else:
            level = self._type_default(question.question_type)
            confidence = 0.38
            reason = f"No recognized action verb; used the {question.question_type} question-type default."
        difficulty, difficulty_reason = self._difficulty(question)
        return QuestionClassification(level, confidence, reason, difficulty, difficulty_reason)

    @staticmethod
    def _type_default(question_type: str) -> BloomLevel:
        return {
            "mcq": BloomLevel.UNDERSTAND,
            "numerical": BloomLevel.APPLY,
            "short_answer": BloomLevel.UNDERSTAND,
            "descriptive": BloomLevel.ANALYZE,
            "coding": BloomLevel.APPLY,
        }[question_type]

    @staticmethod
    def _difficulty(question: QuestionDraft) -> tuple[Difficulty, str]:
        """Estimate workload cues only; this deliberately does not use Bloom level."""
        text = f"{question.question} {question.fields}".casefold()
        score = 0
        if len(question.question.split()) >= 35:
            score += 1
        if len(re.findall(r"\b(if|given|subject to|constraint|case|prove|derive|multiple|all of the following)\b", text)) >= 2:
            score += 1
        if question.question_type in {"descriptive", "coding"}:
            score += 1
        if question.marks is not None:
            score += int(question.marks >= 6) + int(question.marks >= 10)
        difficulty = Difficulty.EASY if score == 0 else Difficulty.MEDIUM if score <= 2 else Difficulty.HARD
        return difficulty, "Estimated from response workload, constraints, question type, and marks; independent of Bloom level."
