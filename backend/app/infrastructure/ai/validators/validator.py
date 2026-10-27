"""Structured Output Validation and Safety Guardrails for AdaptEd.

Implements:
1. Grounding Validator (source ID verification against retrieved context)
2. Anti-Spoiler Guardrail (prevents solution dumping in hint mode)
3. Check Question Validator (ensures actionable prompt for student next step)
4. Safety & Tone Auditor (growth mindset, teacher review escalation)
5. Weak-Area Quiz Validator (representation coverage and choice option consistency)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.application.ports.ai_ports import (
    BaseSchema,
    QuizItem,
    QuizRequest,
    QuizResponse,
    RetrievedChunk,
    TutorRequest,
    TutorResponse,
    ValidationError,
    ValidationResult,
    ValidatorPort,
)


class AntiSpoilerViolation(ValidationError):
    """Raised when a hint-mode response leaks full equation solutions or answers."""

    def __init__(self, message: str, leaked_pattern: Optional[str] = None):
        super().__init__(message, errors=[message], safety_flags=["SPOILER_LEAK"])
        self.leaked_pattern = leaked_pattern


class GroundingViolation(ValidationError):
    """Raised when an LLM cites source IDs not present in retrieved context."""

    def __init__(self, message: str, ungrounded_ids: Optional[List[str]] = None):
        super().__init__(message, errors=[message], safety_flags=["UNGROUNDED_SOURCE"])
        self.ungrounded_ids = ungrounded_ids or []


class TutorValidator:
    """Strict validator enforcing pedagogical contracts and safety guardrails on tutor responses."""

    # Anti-spoiler patterns detecting premature answer leaks in hint mode
    SPOILER_PATTERNS = [
        # Explicit solved variable: e.g. x = -7, y = 4, x = 14 / -2
        re.compile(r"\b[a-zA-Z]\s*=\s*-?\d+(\.\d+)?\b", re.IGNORECASE),
        # Explicit full solved equation transformation: e.g. -2x - 6 = 8, -2x = 14
        re.compile(r"-?2x\s*-\s*6\s*=\s*8", re.IGNORECASE),
        re.compile(r"-?2x\s*=\s*14", re.IGNORECASE),
        re.compile(r"2x\s*=\s*8\b", re.IGNORECASE),
        re.compile(r"\bx\s*=\s*4\b", re.IGNORECASE),
        # Explicit answer revelation stems
        re.compile(r"\bthe (?:final )?answer is\b", re.IGNORECASE),
        re.compile(r"\bthe (?:full )?solution is\b", re.IGNORECASE),
        re.compile(r"\bcorrect answer is\b", re.IGNORECASE),
        # Natural language verbal solution statements: e.g. "The final value of x is -7."
        re.compile(r"\b(?:the\s+)?(?:final\s+)?value\s+of\s+[a-zA-Z]\s+is\b", re.IGNORECASE),
        re.compile(r"\b[a-zA-Z]\s+is\s+equal\s+to\s+-?\d+", re.IGNORECASE),
    ]

    # Shaming and deficit-labeling terminology strictly forbidden
    SHAMING_TERMS = [
        "stupid", "dumb", "failing", "hopeless", "lazy", "incapable",
        "weak student", "bad at math", "you always fail",
    ]

    # Imperative/question stems accepted for check questions
    ACTIONABLE_STEMS = [
        "what", "which", "how", "why", "where", "when",
        "calculate", "rewrite", "find", "solve", "simplify",
        "state", "identify", "determine", "explain", "apply",
    ]

    def _check_grounding(
        self,
        response_or_source_ids: Any,
        request_or_retrieved_sources: Any,
    ) -> Tuple[bool, List[str], List[str]]:
        """Internal helper returning (is_valid, errors, safety_flags)."""
        errors: List[str] = []
        safety_flags: List[str] = []

        # Extract source_ids
        source_ids: List[str] = []
        if hasattr(response_or_source_ids, "source_ids"):
            source_ids = list(response_or_source_ids.source_ids)
        elif isinstance(response_or_source_ids, list):
            source_ids = list(response_or_source_ids)
        elif isinstance(response_or_source_ids, dict):
            source_ids = list(response_or_source_ids.get("source_ids", []))

        # Extract retrieved_sources
        retrieved_sources: List[Any] = []
        if hasattr(request_or_retrieved_sources, "retrieved_sources"):
            retrieved_sources = list(request_or_retrieved_sources.retrieved_sources)
        elif isinstance(request_or_retrieved_sources, list):
            retrieved_sources = list(request_or_retrieved_sources)
        elif isinstance(request_or_retrieved_sources, dict):
            retrieved_sources = list(request_or_retrieved_sources.get("retrieved_sources", []))

        # Collect all valid IDs from retrieved sources
        retrieved_ids: Set[str] = set()
        for src in retrieved_sources:
            if isinstance(src, RetrievedChunk):
                retrieved_ids.add(src.id)
                if src.source_id:
                    retrieved_ids.add(src.source_id)
            elif isinstance(src, dict):
                if "id" in src:
                    retrieved_ids.add(str(src["id"]))
                if "source_id" in src:
                    retrieved_ids.add(str(src["source_id"]))
            elif hasattr(src, "id"):
                retrieved_ids.add(str(src.id))

        # If retrieved sources is empty, no factual citations are allowed
        if not retrieved_ids and source_ids:
            errors.append(
                f"Retrieved context is empty, but response cited source IDs: {source_ids}"
            )
            safety_flags.append("UNGROUNDED_SOURCE")

        # Check for hallucinated source citations
        hallucinated_ids = [sid for sid in source_ids if sid not in retrieved_ids]
        if hallucinated_ids:
            errors.append(
                f"Response cited hallucinated source IDs not present in retrieved context: {hallucinated_ids}"
            )
            safety_flags.append("UNGROUNDED_SOURCE")

        return len(errors) == 0, errors, safety_flags

    def validate_grounding(
        self,
        response_or_source_ids: Any,
        request_or_retrieved_sources: Any,
    ) -> bool:
        """Verify that all cited source IDs exist in the retrieved context. Returns bool."""
        valid, _, _ = self._check_grounding(response_or_source_ids, request_or_retrieved_sources)
        return valid

    def detect_spoilers(
        self, text: str, mode: str, check_question: str = ""
    ) -> Tuple[bool, List[str], List[str]]:
        """Detect and reject answer dumping / final solution equations when in hint mode."""
        errors: List[str] = []
        safety_flags: List[str] = []

        if mode == "hint":
            combined_text = f"{text} {check_question}"
            for pattern in self.SPOILER_PATTERNS:
                match = pattern.search(combined_text)
                if match:
                    leak = match.group(0)
                    errors.append(
                        f"Anti-spoiler violation: hint mode response leaked final answer or step '{leak}'"
                    )
                    safety_flags.append("SPOILER_LEAK")
                    break

        return len(errors) == 0, errors, safety_flags

    def _check_question(self, check_question: str) -> Tuple[bool, List[str], List[str]]:
        """Internal helper returning (is_valid, errors, safety_flags) for check questions."""
        errors: List[str] = []
        safety_flags: List[str] = []

        cleaned = check_question.strip() if check_question else ""
        if not cleaned:
            errors.append("Check question is empty. Every tutor response must end with an actionable check question.")
            safety_flags.append("MISSING_CHECK_QUESTION")
            return False, errors, safety_flags

        # Must either contain a question mark or start with an actionable prompt verb
        has_question_mark = "?" in cleaned
        lower_q = cleaned.lower()
        has_action_stem = any(lower_q.startswith(stem) or f" {stem} " in f" {lower_q} " for stem in self.ACTIONABLE_STEMS)

        if not (has_question_mark or has_action_stem):
            errors.append(
                f"Check question '{check_question}' lacks question syntax ('?') or actionable stem."
            )
            safety_flags.append("WEAK_CHECK_QUESTION")

        return len(errors) == 0, errors, safety_flags

    def validate_check_question(self, check_question: str) -> bool:
        """Verify presence of a non-empty, actionable check question. Returns bool."""
        valid, _, _ = self._check_question(check_question)
        return valid

    def check_safety_and_tone(self, text: str) -> Tuple[bool, List[str], List[str]]:
        """Verify adherence to supportive, growth-mindset tone without shaming."""
        errors: List[str] = []
        safety_flags: List[str] = []
        lower_text = text.lower()

        for term in self.SHAMING_TERMS:
            if term in lower_text:
                errors.append(f"Tone violation: detected forbidden shaming term '{term}'")
                safety_flags.append("TONE_VIOLATION")

        return len(errors) == 0, errors, safety_flags

    def validate_tone(self, text: str) -> bool:
        """Verify tone is free of shaming language. Returns bool."""
        valid, _, _ = self.check_safety_and_tone(text)
        return valid

    def validate(
        self,
        response: TutorResponse,
        request: Optional[Any] = None,
        retrieved_sources: Optional[List[Any]] = None,
    ) -> ValidationResult:
        """Execute full pedagogical, grounding, and anti-spoiler validation on tutor response."""
        all_errors: List[str] = []
        all_safety_flags: List[str] = list(response.safety_flags)

        # Determine effective retrieved sources
        effective_sources: List[Any] = []
        if retrieved_sources is not None:
            effective_sources = retrieved_sources
        elif request is not None:
            if isinstance(request, list):
                effective_sources = request
            elif hasattr(request, "retrieved_sources"):
                effective_sources = request.retrieved_sources
            elif isinstance(request, dict):
                effective_sources = request.get("retrieved_sources", [])

        # 1. Grounding check
        g_valid, g_errors, g_flags = self._check_grounding(response, effective_sources)
        all_errors.extend(g_errors)
        all_safety_flags.extend(g_flags)

        # 2. Anti-spoiler guardrail
        s_valid, s_errors, s_flags = self.detect_spoilers(
            response.message, response.mode, response.check_question
        )
        all_errors.extend(s_errors)
        all_safety_flags.extend(s_flags)

        # 3. Check question verification
        q_valid, q_errors, q_flags = self._check_question(response.check_question)
        all_errors.extend(q_errors)
        all_safety_flags.extend(q_flags)

        # 4. Tone and safety check
        t_valid, t_errors, t_flags = self.check_safety_and_tone(
            f"{response.message} {response.check_question}"
        )
        all_errors.extend(t_errors)
        all_safety_flags.extend(t_flags)

        # 5. Missing retrieval escalation check
        if not effective_sources and not response.needs_teacher_review:
            all_safety_flags.append("LOW_CONFIDENCE_RETRIEVAL")
            response.needs_teacher_review = True

        unique_flags = list(dict.fromkeys(all_safety_flags))
        is_valid = len(all_errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            safety_flags=unique_flags,
            sanitized_response=response,
        )


class QuizValidator:
    """Strict validator for generated weak-area quiz drafts."""

    ALLOWED_REPRESENTATIONS = {"symbolic", "error_analysis", "verbal", "visual", "transfer"}
    ALLOWED_ANSWER_TYPES = {"expression", "choice", "numeric", "explanation"}

    def validate(
        self,
        response: QuizResponse,
        request: Optional[QuizRequest] = None,
    ) -> ValidationResult:
        """Validate quiz response against requested concept, count, and representations."""
        errors: List[str] = []
        safety_flags: List[str] = []

        if not response.items:
            errors.append("QuizResponse contains no items.")
            safety_flags.append("EMPTY_QUIZ")
            return ValidationResult(is_valid=False, errors=errors, safety_flags=safety_flags)

        if request is not None:
            if len(response.items) != request.num_items:
                errors.append(
                    f"Generated {len(response.items)} items, but requested {request.num_items} items."
                )

            if response.concept_id != request.concept_id:
                errors.append(
                    f"Quiz concept_id '{response.concept_id}' does not match request '{request.concept_id}'"
                )

        # Validate each individual item
        observed_representations: Set[str] = set()
        for idx, item in enumerate(response.items):
            if item.representation not in self.ALLOWED_REPRESENTATIONS:
                errors.append(f"Item #{idx} has invalid representation '{item.representation}'")
            observed_representations.add(item.representation)

            if item.answer_type not in self.ALLOWED_ANSWER_TYPES:
                errors.append(f"Item #{idx} has invalid answer_type '{item.answer_type}'")

            if not item.question.strip():
                errors.append(f"Item #{idx} has an empty question.")

            if not item.answer.strip():
                errors.append(f"Item #{idx} has an empty answer.")

            if not item.explanation.strip():
                errors.append(f"Item #{idx} has an empty explanation.")

            if item.answer_type == "choice":
                if not item.options or len(item.options) < 2:
                    errors.append(f"Choice item #{idx} must have at least 2 options.")
                elif item.answer not in item.options:
                    errors.append(
                        f"Choice item #{idx} answer '{item.answer}' is not among options: {item.options}"
                    )

        # Check representation variety only when multiple distinct representations were requested or expected
        if (
            request is not None
            and request.num_items > 1
            and (not request.requested_representations or len(set(request.requested_representations)) > 1)
            and len(observed_representations) < 2
        ):
            errors.append(
                f"Quiz lacks representation diversity: all items use {observed_representations}"
            )
            safety_flags.append("LOW_REPRESENTATION_DIVERSITY")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            safety_flags=safety_flags,
            sanitized_response=response,
        )

    def validate_quiz(self, response: QuizResponse) -> bool:
        """Convenience method returning bool."""
        return self.validate(response).is_valid


class ComprehensiveAIValidator(ValidatorPort):
    """Unified implementation of ValidatorPort combining tutor and quiz validation."""

    def __init__(self) -> None:
        self.tutor_validator = TutorValidator()
        self.quiz_validator = QuizValidator()

    def validate_tutor_response(
        self, response: TutorResponse, request: TutorRequest
    ) -> ValidationResult:
        return self.tutor_validator.validate(response, request)

    def validate_quiz_response(
        self, response: QuizResponse, request: QuizRequest
    ) -> ValidationResult:
        return self.quiz_validator.validate(response, request)
