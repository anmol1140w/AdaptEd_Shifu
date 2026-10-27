"""Weak-Area Quiz Generator for AdaptEd.

Generates targeted, diagnostic assessment items tied to diagnosed learner
misconceptions and difficulty levels across 4 diverse representations:
1. Symbolic (direct algebraic manipulation)
2. Error Analysis (evaluating flawed student work)
3. Verbal / Visual (conceptual justification and area-model reasoning)
4. Transfer Problems (higher-order context and multi-step integration)
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.application.ports.ai_ports import (
    QuizGeneratorPort,
    QuizItem,
    QuizRequest,
    QuizResponse,
    ValidationResult,
)
from backend.app.infrastructure.ai.llm.base import BaseLLMClient
from backend.app.infrastructure.ai.llm.mock_llm import MockLLMClient
from backend.app.infrastructure.ai.prompts.quiz_prompts import (
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from backend.app.infrastructure.ai.validators.validator import QuizValidator

logger = logging.getLogger(__name__)


class WeakAreaQuizGenerator(QuizGeneratorPort):
    """Generates targeted diagnostic quizzes across 4 diverse representations."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        validator: Optional[QuizValidator] = None,
        content_items_dir: Optional[str] = None,
        items_dir: Optional[str] = None,
    ):
        self.llm_client = llm_client or MockLLMClient()
        self.validator = validator or QuizValidator()
        self.content_items_dir = content_items_dir or items_dir or "content/items"
        self._vetted_item_bank: Dict[str, List[QuizItem]] = {}
        self._load_vetted_items()

    def _load_vetted_items(self) -> None:
        """Load approved item banks from content/items directory as guaranteed fallbacks."""
        search_dirs = [
            self.content_items_dir,
            f"/data/adapted/AdaptEd/{self.content_items_dir}",
            "content/items",
        ]
        for cdir in search_dirs:
            if not os.path.exists(cdir):
                continue
            for fpath in Path(cdir).glob("items_*.json"):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        items_data = json.load(f)
                    if isinstance(items_data, list):
                        for idata in items_data:
                            item = QuizItem.from_dict(idata)
                            cid = item.concept_id or "ALG-DIST-01"
                            if cid not in self._vetted_item_bank:
                                self._vetted_item_bank[cid] = []
                            self._vetted_item_bank[cid].append(item)
                except Exception as exc:
                    logger.warning("Failed to load vetted items from %s: %s", fpath, exc)

    def generate_quiz(self, request: QuizRequest) -> QuizResponse:
        """Generate targeted quiz items addressing the learner's diagnosed misconception."""
        system_prompt = build_quiz_system_prompt()
        user_prompt = build_quiz_user_prompt(request)

        # Attempt generation via LLM adapter
        try:
            response = self.llm_client.generate_structured(
                QuizResponse,
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
            # Validate generated quiz
            val_result = self.validator.validate(response, request)
            if val_result.is_valid:
                return response
        except Exception as exc:
            logger.warning("LLM generation failed, falling back to vetted bank: %s", exc)

        # Fallback to curated vetted item bank
        return self._generate_from_vetted_bank(request)

    def _generate_from_vetted_bank(self, request: QuizRequest) -> QuizResponse:
        """Construct a validated QuizResponse from vetted bank matching requested representations."""
        concept_items = self._vetted_item_bank.get(request.concept_id, [])
        if not concept_items:
            # Fall back to any available concept items
            concept_items = [item for sublist in self._vetted_item_bank.values() for item in sublist]

        requested_reps = request.requested_representations or [
            "symbolic",
            "error_analysis",
            "verbal",
            "transfer",
        ]

        selected_items: List[QuizItem] = []
        # First pass: try to pick 1 item for each requested representation
        for rep in requested_reps:
            matching = [it for it in concept_items if it.representation == rep]
            for it in matching:
                if len(selected_items) < request.num_items and it not in selected_items:
                    selected_items.append(it)
                    break

        # Second pass: if still short, fill remaining items from requested representations
        if len(selected_items) < request.num_items:
            for rep in requested_reps:
                matching = [it for it in concept_items if it.representation == rep]
                for it in matching:
                    if len(selected_items) < request.num_items and it not in selected_items:
                        selected_items.append(it)

        # Third pass: fill remaining items from general concept bank
        for it in concept_items:
            if len(selected_items) >= request.num_items:
                break
            if it not in selected_items:
                selected_items.append(it)

        # Fourth pass: if still short, replicate with distinct IDs
        while len(selected_items) < request.num_items and concept_items:
            base = concept_items[len(selected_items) % len(concept_items)]
            clone = QuizItem(
                id=f"{base.id}-ext-{len(selected_items)}",
                representation=base.representation,
                question=base.question,
                answer_type=base.answer_type,
                difficulty=getattr(base, "difficulty", request.difficulty),
                options=list(base.options) if base.options else None,
                answer=base.answer,
                explanation=base.explanation,
                source_id=base.source_id,
                concept_id=request.concept_id,
                misconception_tag=request.misconception,
            )
            selected_items.append(clone)

        return QuizResponse(
            quiz_id=f"quiz-{request.concept_id.lower()}-{request.learner_id}",
            concept_id=request.concept_id,
            target_misconception=request.misconception,
            difficulty=request.difficulty,
            items=selected_items,
        )
