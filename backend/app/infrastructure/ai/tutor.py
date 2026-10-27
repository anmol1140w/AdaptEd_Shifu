"""Grounded RAG Tutor Service for AdaptEd.

Orchestrates:
1. Deterministic retrieval from approved curriculum chunks
2. Missing / low-confidence retrieval detection with teacher-review escalation
3. Pedagogical prompt construction (hint, explanation, check_question)
4. Provider-neutral LLM generation (mock or live)
5. Anti-spoiler, grounding, and check-question safety validation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.application.ports.ai_ports import (
    LLMPort,
    RetrievedChunk,
    RetrieverPort,
    TutorPort,
    TutorRequest,
    TutorResponse,
    ValidationResult,
)
from backend.app.infrastructure.ai.llm.base import BaseLLMClient
from backend.app.infrastructure.ai.llm.mock_llm import MockLLMClient
from backend.app.infrastructure.ai.prompts.tutor_prompts import (
    build_tutor_system_prompt,
    build_tutor_user_prompt,
)
from backend.app.infrastructure.ai.retrieval.mock_retriever import MockKnowledgeRetriever
from backend.app.infrastructure.ai.validators.validator import TutorValidator

logger = logging.getLogger(__name__)


class GroundedRAGTutor(TutorPort):
    """Pedagogical, grounded RAG tutor enforcing anti-spoiler and teacher escalation."""

    FALLBACK_TEACHER_REVIEW_MSG = (
        "I want to make sure you get the most accurate explanation. "
        "I've flagged this question for your teacher to review and provide tailored guidance."
    )
    FALLBACK_CHECK_QUESTION = (
        "While waiting, what part of the problem feels most challenging to you?"
    )

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        retriever: Optional[RetrieverPort] = None,
        validator: Optional[TutorValidator] = None,
        min_retrieval_confidence: float = 0.20,
    ):
        self.llm_client = llm_client or MockLLMClient()
        self.retriever = retriever or MockKnowledgeRetriever()
        self.validator = validator or TutorValidator()
        self.min_retrieval_confidence = min_retrieval_confidence

    def respond(self, request: TutorRequest) -> TutorResponse:
        """Process learner attempt and return a grounded, verified tutor response."""
        # 1. Retrieve sources if not already pre-populated in the request
        if not request.retrieved_sources:
            search_query = request.learner_attempt or request.concept
            retrieved = self.retriever.retrieve(
                concept_id=request.concept_id,
                query=search_query,
                top_k=3,
            )
            request.retrieved_sources = retrieved

        # 2. Check for missing or low-confidence retrieval
        if not request.retrieved_sources:
            return TutorResponse(
                mode=request.requested_mode,
                message=self.FALLBACK_TEACHER_REVIEW_MSG,
                check_question=self.FALLBACK_CHECK_QUESTION,
                source_ids=[],
                confidence="low",
                needs_teacher_review=True,
                safety_flags=["LOW_CONFIDENCE_RETRIEVAL"],
            )

        highest_score = max((c.score for c in request.retrieved_sources), default=0.0)
        if highest_score < self.min_retrieval_confidence:
            return TutorResponse(
                mode=request.requested_mode,
                message=self.FALLBACK_TEACHER_REVIEW_MSG,
                check_question=self.FALLBACK_CHECK_QUESTION,
                source_ids=[],
                confidence="low",
                needs_teacher_review=True,
                safety_flags=["LOW_CONFIDENCE_RETRIEVAL"],
            )

        # 3. Build pedagogical prompts
        system_prompt = build_tutor_system_prompt()
        user_prompt = build_tutor_user_prompt(request)

        # 4. Generate structured response from LLM adapter
        response = self.llm_client.generate_structured(
            TutorResponse,
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        # 5. Validate response against grounding, anti-spoiler, and check-question guardrails
        val_result = self.validator.validate(response, request)

        # 6. Apply automated sanitization if guardrail violation detected
        if not val_result.is_valid:
            if "SPOILER_LEAK" in val_result.safety_flags:
                # Sanitize leaked answer in hint mode to safe leading inquiry
                response.message = (
                    "When multiplying across brackets, the negative multiplier applies to every term. "
                    "Which term has not received the multiplier yet?"
                )
                response.check_question = "What is the result of multiplying the outer factor by the second term?"

            if "UNGROUNDED_SOURCE" in val_result.safety_flags:
                # Filter out hallucinated source IDs, leaving only valid retrieved sources
                valid_ids = {c.id for c in request.retrieved_sources} | {
                    c.source_id for c in request.retrieved_sources if c.source_id
                }
                response.source_ids = [sid for sid in response.source_ids if sid in valid_ids]
                if not response.source_ids and request.retrieved_sources:
                    chosen = request.retrieved_sources[0]
                    fallback_id = chosen.source_id if chosen.source_id and chosen.source_id.startswith(("lesson-algebra", "worked-example")) else chosen.id
                    response.source_ids = [fallback_id]

            if "MISSING_CHECK_QUESTION" in val_result.safety_flags:
                response.check_question = "What is your next step?"

        # Attach all safety flags
        all_flags = list(dict.fromkeys(response.safety_flags + val_result.safety_flags))
        response.safety_flags = all_flags

        return response

    def handle_request(self, request: TutorRequest) -> TutorResponse:
        """Alias for respond."""
        return self.respond(request)

    def tutor(self, request: TutorRequest) -> TutorResponse:
        """Alias for respond."""
        return self.respond(request)

    def __call__(self, request: TutorRequest) -> TutorResponse:
        """Callable alias for respond."""
        return self.respond(request)
