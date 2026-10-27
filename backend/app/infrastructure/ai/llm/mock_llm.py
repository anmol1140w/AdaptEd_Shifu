"""Deterministic Mock LLM Adapter for AdaptEd.

Pre-programmed for benchmark demo scenarios (Riya, Arjun, Missing Retrieval)
alongside test simulation modes (spoiler leak, ungrounded sources, tone violations)
and deterministic fallback generation for arbitrary mathematics prompts.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Type, TypeVar

from backend.app.application.ports.ai_ports import (
    BaseSchema,
    QuizItem,
    QuizRequest,
    QuizResponse,
    TutorRequest,
    TutorResponse,
    ValidationError,
)
from backend.app.infrastructure.ai.llm.base import BaseLLMClient

T = TypeVar("T", bound=BaseSchema)


class MockLLMClient(BaseLLMClient):
    """Deterministic, 100% offline mock LLM client with benchmark and simulation modes."""

    def __init__(
        self,
        default_model: str = "mock-gpt-4o",
        simulation_mode: Optional[str] = None,
        simulate_spoiler: bool = False,
        **kwargs: Any,
    ):
        self.default_model = default_model
        self.simulation_mode = simulation_mode
        if simulate_spoiler:
            self.simulation_mode = "spoiler_leak"
        self.call_history: List[Dict[str, Any]] = []

    def set_simulation_mode(self, mode: Optional[str]) -> None:
        """Configure simulation mode for testing validator guardrails:

        - 'spoiler_leak': Leaks final equation answer in hint mode
        - 'ungrounded_source': Leaks hallucinated source ID 'lesson-geometry-99'
        - 'missing_check_question': Sets check_question to empty string
        - 'shaming_tone': Includes shaming words
        - 'contradictory': Sets contradictory sources flag and teacher review
        """
        self.simulation_mode = mode

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Generate unstructured text completion."""
        self.call_history.append({"prompt": prompt, "system_prompt": system_prompt, "kwargs": kwargs})

        # Check simulation mode overrides
        if self.simulation_mode == "spoiler_leak":
            return "The final answer is x = -7. Expanding -2(x + 3) = 8 gives -2x - 6 = 8."
        if self.simulation_mode == "shaming_tone":
            return "You are stupid at math for writing -2x + 3."

        # Riya Distributive Misconception
        lower_prompt = prompt.lower()
        if "riya" in lower_prompt or "-2(x + 3)" in lower_prompt or "alg-dist-01" in lower_prompt:
            if "explanation" in lower_prompt:
                return (
                    "When distributing -2 across (x + 3), the multiplier -2 applies to both terms: "
                    "(-2 * x) + (-2 * 3) = -2x - 6. Both terms receive the multiplier and sign change."
                )
            return (
                "When you multiply a bracket by -2, the -2 applies to every term inside it. "
                "Which term has not received the -2 yet? What is -2 multiplied by +3?"
            )

        # Arjun Transfer Scenario
        if "arjun" in lower_prompt or "transfer" in lower_prompt or "alg-twostep-01" in lower_prompt:
            return (
                "Since you have mastered basic two-step equations, try this transfer challenge: "
                "Solve -3(2x - 4) + 5x = 22. What is your first step to expand the parentheses?"
            )

        return (
            "Focus on applying the inverse operation to isolate the variable term first. "
            "What operation undoes the constant term?"
        )

    def generate_structured(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured completion adhering to schema type."""
        self.call_history.append({
            "schema": schema.__name__,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "kwargs": kwargs,
        })

        if schema is TutorResponse:
            response_dict = self._generate_tutor_response_dict(prompt)
            return schema.model_validate(response_dict)

        if schema is QuizResponse:
            response_dict = self._generate_quiz_response_dict(prompt)
            return schema.model_validate(response_dict)

        # Generic structured fallback: attempt to extract JSON or create default
        try:
            return schema.model_validate({})
        except Exception:
            raise ValidationError(f"MockLLMClient does not support arbitrary schema: {schema}")

    def _generate_tutor_response_dict(self, prompt: str) -> Dict[str, Any]:
        """Construct deterministic dictionary payload for TutorResponse."""
        lower_p = prompt.lower()

        # 1. Check simulation modes
        if self.simulation_mode == "spoiler_leak":
            return {
                "mode": "hint",
                "message": "The complete simplified equation is -2x - 6 = 8, so x = -7.",
                "check_question": "Does x = -7 satisfy the equation?",
                "source_ids": ["lesson-algebra-03"],
                "confidence": "high",
                "needs_teacher_review": False,
                "safety_flags": [],
            }

        if self.simulation_mode == "ungrounded_source":
            return {
                "mode": "hint",
                "message": "When you multiply a bracket by -2, the -2 applies to every term inside it.",
                "check_question": "What is -2 multiplied by +3?",
                "source_ids": ["lesson-geometry-99"],  # Hallucinated ID!
                "confidence": "high",
                "needs_teacher_review": False,
                "safety_flags": [],
            }

        if self.simulation_mode == "missing_check_question":
            return {
                "mode": "hint",
                "message": "When you multiply a bracket by -2, the -2 applies to every term inside it.",
                "check_question": "",  # Empty!
                "source_ids": ["lesson-algebra-03"],
                "confidence": "high",
                "needs_teacher_review": False,
                "safety_flags": [],
            }

        if self.simulation_mode == "shaming_tone":
            return {
                "mode": "hint",
                "message": "You are stupid at math for writing -2x + 3 instead of -2x - 6.",
                "check_question": "Why did you make that dumb error?",
                "source_ids": ["lesson-algebra-03"],
                "confidence": "high",
                "needs_teacher_review": False,
                "safety_flags": [],
            }

        if self.simulation_mode == "contradictory":
            return {
                "mode": "explanation",
                "message": "The retrieved sources offer contradictory definitions for this term.",
                "check_question": "Would you like your teacher to clarify?",
                "source_ids": [],
                "confidence": "low",
                "needs_teacher_review": True,
                "safety_flags": ["CONTRADICTORY_SOURCES"],
            }

        # 2. Check for missing / low retrieval scenario
        if (
            "missing_sources" in lower_p
            or "empty_retrieval" in lower_p
            or "retrieved sources: []" in lower_p
            or "retrieved sources: none" in lower_p
            or "none / empty" in lower_p
            or "retrieval confidence: low" in lower_p
            or "unknown concept" in lower_p
            or "sources: none" in lower_p
            or "confidence: low" in lower_p
        ):
            return {
                "mode": "hint",
                "message": (
                    "I want to make sure you get the most accurate explanation. "
                    "I've flagged this question for your teacher to review and provide tailored guidance."
                ),
                "check_question": "While waiting, what part of the problem feels most challenging to you?",
                "source_ids": [],
                "confidence": "low",
                "needs_teacher_review": True,
                "safety_flags": ["LOW_CONFIDENCE_RETRIEVAL"],
            }

        # Determine requested mode from prompt
        requested_mode = "hint"
        if "mode: explanation" in lower_p or "requested_mode\": \"explanation\"" in lower_p:
            requested_mode = "explanation"
        elif "mode: check_question" in lower_p or "requested_mode\": \"check_question\"" in lower_p:
            requested_mode = "check_question"

        # 3. Benchmark Case 1: Riya Scenario (Distributive Property Misconception)
        if (
            "riya" in lower_p
            or "-2(x + 3)" in lower_p
            or "alg-dist-01" in lower_p
            or "distributive" in lower_p
        ):
            if requested_mode == "hint":
                return {
                    "mode": "hint",
                    "message": (
                        "When you multiply a bracket by -2, the -2 applies to every term inside it. "
                        "Which term has not received the -2 yet?"
                    ),
                    "check_question": "What is -2 multiplied by +3?",
                    "source_ids": ["lesson-algebra-03"],
                    "confidence": "high",
                    "needs_teacher_review": False,
                    "safety_flags": [],
                }
            elif requested_mode == "explanation":
                return {
                    "mode": "explanation",
                    "message": (
                        "The Distributive Property requires multiplying the factor outside parentheses "
                        "by every term inside: a(b + c) = ab + ac. When the factor is negative (-2), "
                        "multiplying each term gives (-2 * x) + (-2 * 3) = -2x - 6. "
                        "Remember that multiplying a negative by a positive number produces a negative product."
                    ),
                    "check_question": "Rewrite -3(y + 4) using the same rule.",
                    "source_ids": ["lesson-algebra-03", "worked-example-07"],
                    "confidence": "high",
                    "needs_teacher_review": False,
                    "safety_flags": [],
                }
            else:  # check_question mode
                return {
                    "mode": "check_question",
                    "message": "Let's check your understanding of multiplying signed numbers across parentheses.",
                    "check_question": "What is -2 multiplied by +3?",
                    "source_ids": ["lesson-algebra-03"],
                    "confidence": "high",
                    "needs_teacher_review": False,
                    "safety_flags": [],
                }

        # 4. Benchmark Case 2: Arjun Scenario (Transfer / Mastery)
        if "arjun" in lower_p or "alg-twostep-01" in lower_p or "two-step" in lower_p or "transfer" in lower_p:
            return {
                "mode": requested_mode,
                "message": (
                    "Great work on standard two-step equations. Let's tackle a transfer problem "
                    "that combines brackets with variable isolation: -3(2x - 4) + 5x = 22."
                ),
                "check_question": "What is your first step to expand the parentheses?",
                "source_ids": ["lesson-algebra-04", "worked-example-08"],
                "confidence": "high",
                "needs_teacher_review": False,
                "safety_flags": [],
            }

        # 5. Generic Deterministic Fallback
        return {
            "mode": requested_mode,
            "message": "Remember to apply inverse operations in reverse order to isolate the variable.",
            "check_question": "What operation undoes the addition on the left side?",
            "source_ids": ["lesson-algebra-04"],
            "confidence": "high",
            "needs_teacher_review": False,
            "safety_flags": [],
        }

    def _generate_quiz_response_dict(self, prompt: str) -> Dict[str, Any]:
        """Construct deterministic dictionary payload for QuizResponse."""
        lower_p = prompt.lower()

        # Check concept ID
        concept_id = "ALG-DIST-01"
        if "alg-twostep-01" in lower_p or "two-step" in lower_p:
            concept_id = "ALG-TWOSTEP-01"

        misconception = "loses the negative sign"
        if "inverse" in lower_p:
            misconception = "incorrect inverse operation order"

        difficulty = "medium"
        if "transfer" in lower_p or "hard" in lower_p or "arjun" in lower_p:
            difficulty = "transfer"

        # Determine item count
        num_items = 3
        match_num = re.search(r"num_items[:\"\s=]+(\d+)", lower_p)
        if match_num:
            num_items = int(match_num.group(1))

        if concept_id == "ALG-DIST-01":
            if difficulty == "transfer" or "transfer" in lower_p or "arjun" in lower_p:
                candidate_items = [
                    {
                        "id": "item-dist-trans-01",
                        "representation": "transfer",
                        "difficulty": "transfer",
                        "question": "Solve the equation -3(2x - 1) = 15. What is the value of x?",
                        "answer_type": "numeric",
                        "options": None,
                        "answer": "-2",
                        "explanation": "Expand: -6x + 3 = 15. Subtract 3: -6x = 12. Divide by -6: x = -2.",
                        "source_id": "worked-example-07",
                        "concept_id": "ALG-DIST-01",
                        "misconception_tag": "loses the negative sign",
                    },
                    {
                        "id": "item-dist-trans-02",
                        "representation": "transfer",
                        "difficulty": "transfer",
                        "question": "Expand and combine like terms in the multi-step expression: -2(3x + 4) + 5x - 7",
                        "answer_type": "expression",
                        "options": None,
                        "answer": "-x - 15",
                        "explanation": "Distribute: -6x - 8 + 5x - 7. Combine like terms: (-6x + 5x) + (-8 - 7) = -x - 15.",
                        "source_id": "lesson-algebra-03",
                        "concept_id": "ALG-DIST-01",
                        "misconception_tag": "loses the negative sign",
                    },
                    {
                        "id": "item-dist-sym-01",
                        "representation": "symbolic",
                        "difficulty": "hard",
                        "question": "Expand and simplify the expression: -3(x + 4)",
                        "answer_type": "choice",
                        "options": ["-3x + 12", "-3x - 12", "-3x + 4", "3x - 12"],
                        "answer": "-3x - 12",
                        "explanation": "Distribute -3 to x and -3 to +4: -3*x + (-3)*4 = -3x - 12.",
                        "source_id": "lesson-algebra-03",
                        "concept_id": "ALG-DIST-01",
                        "misconception_tag": "loses the negative sign",
                    },
                ]
            else:
                candidate_items = [
                    {
                        "id": "item-dist-sym-01",
                        "representation": "symbolic",
                        "difficulty": "medium",
                        "question": "Expand and simplify the expression: -3(x + 4)",
                        "answer_type": "choice",
                        "options": ["-3x + 12", "-3x - 12", "-3x + 4", "3x - 12"],
                        "answer": "-3x - 12",
                        "explanation": "Distribute -3 to x and -3 to +4: -3*x + (-3)*4 = -3x - 12.",
                        "source_id": "lesson-algebra-03",
                        "concept_id": "ALG-DIST-01",
                        "misconception_tag": "loses the negative sign",
                    },
                    {
                        "id": "item-dist-err-01",
                        "representation": "error_analysis",
                        "difficulty": "medium",
                        "question": "A learner attempted to simplify -2(x + 3) and wrote -2x + 3. What error did the learner make?",
                        "answer_type": "choice",
                        "options": [
                            "The learner forgot to distribute the multiplier -2 to the constant term +3.",
                            "The learner made an error in multiplying -2 by x.",
                            "The learner should have added -2 and 3 before expanding.",
                            "There is no error in the student's solution.",
                        ],
                        "answer": "The learner forgot to distribute the multiplier -2 to the constant term +3.",
                        "explanation": "The distributive property applies to every term inside: -2 * 3 = -6, so the result is -2x - 6.",
                        "source_id": "worked-example-07",
                        "concept_id": "ALG-DIST-01",
                        "misconception_tag": "loses the negative sign",
                    },
                    {
                        "id": "item-dist-verb-01",
                        "representation": "verbal",
                        "difficulty": "medium",
                        "question": "In your own words, explain why the factor outside parentheses must be multiplied by every term inside.",
                        "answer_type": "explanation",
                        "options": None,
                        "answer": "Parentheses group terms together; multiplying the group requires scaling every term inside.",
                        "explanation": "Grouping terms means the whole group is multiplied, so each term is scaled equally.",
                        "source_id": "lesson-algebra-03",
                        "concept_id": "ALG-DIST-01",
                        "misconception_tag": "multiplies only the first term",
                    },
                    {
                        "id": "item-dist-trans-01",
                        "representation": "transfer",
                        "difficulty": "transfer",
                        "question": "Solve the equation -3(2x - 1) = 15. What is the value of x?",
                        "answer_type": "numeric",
                        "options": None,
                        "answer": "-2",
                        "explanation": "Expand: -6x + 3 = 15. Subtract 3: -6x = 12. Divide by -6: x = -2.",
                        "source_id": "worked-example-07",
                        "concept_id": "ALG-DIST-01",
                        "misconception_tag": "loses the negative sign",
                    },
                ]
        else:
            if difficulty == "transfer" or "transfer" in lower_p or "arjun" in lower_p:
                candidate_items = [
                    {
                        "id": "item-twostep-trans-02",
                        "representation": "transfer",
                        "difficulty": "transfer",
                        "question": "Solve the multi-step equation combining distributive property and two-step solving: -3(2x - 4) + 5x = 22. What is x?",
                        "answer_type": "numeric",
                        "options": None,
                        "answer": "-10",
                        "explanation": "Step 1: -6x + 12 + 5x = 22 => -x + 12 = 22 => -x = 10 => x = -10.",
                        "source_id": "worked-example-08",
                        "concept_id": "ALG-TWOSTEP-01",
                        "misconception_tag": "combining brackets and multi-step transfer",
                    },
                    {
                        "id": "item-twostep-trans-01",
                        "representation": "transfer",
                        "difficulty": "hard",
                        "question": "A taxi service charges $4 base fee plus $2.50 per kilometer. For a trip costing $19, what was the distance in km?",
                        "answer_type": "choice",
                        "options": [
                            "4 + 2.50d = 19, so d = 6 km",
                            "2.50 + 4d = 19, so d = 4.125 km",
                            "4d = 19, so d = 4.75 km",
                            "4 + 2.50d = 19, so d = 9.2 km",
                        ],
                        "answer": "4 + 2.50d = 19, so d = 6 km",
                        "explanation": "2.50d + 4 = 19 => 2.50d = 15 => d = 6 km.",
                        "source_id": "lesson-algebra-04",
                        "concept_id": "ALG-TWOSTEP-01",
                        "misconception_tag": "contextual modeling error",
                    },
                    {
                        "id": "item-twostep-sym-01",
                        "representation": "symbolic",
                        "difficulty": "medium",
                        "question": "Solve the two-step equation: 2x + 5 = 13",
                        "answer_type": "numeric",
                        "options": None,
                        "answer": "4",
                        "explanation": "Subtract 5: 2x = 8. Divide by 2: x = 4.",
                        "source_id": "lesson-algebra-04",
                        "concept_id": "ALG-TWOSTEP-01",
                        "misconception_tag": "incorrect inverse operation order",
                    },
                ]
            else:
                candidate_items = [
                    {
                        "id": "item-twostep-sym-01",
                        "representation": "symbolic",
                        "difficulty": "medium",
                        "question": "Solve the two-step equation: 2x + 5 = 13",
                        "answer_type": "numeric",
                        "options": None,
                        "answer": "4",
                        "explanation": "Subtract 5: 2x = 8. Divide by 2: x = 4.",
                        "source_id": "lesson-algebra-04",
                        "concept_id": "ALG-TWOSTEP-01",
                        "misconception_tag": "incorrect inverse operation order",
                    },
                    {
                        "id": "item-twostep-err-01",
                        "representation": "error_analysis",
                        "difficulty": "medium",
                        "question": "In solving 3x + 6 = 21, a student wrote x + 6 = 7. Identify the mistake.",
                        "answer_type": "choice",
                        "options": [
                            "The constant 6 was not divided by 3.",
                            "The student should have multiplied 21 by 3.",
                            "3x divided by 3 is not x.",
                            "There is no mistake.",
                        ],
                        "answer": "The constant 6 was not divided by 3.",
                        "explanation": "When dividing both sides, every term must be divided: 6 / 3 = 2, so x + 2 = 7.",
                        "source_id": "lesson-algebra-04",
                        "concept_id": "ALG-TWOSTEP-01",
                        "misconception_tag": "incorrect inverse operation order",
                    },
                    {
                        "id": "item-twostep-trans-01",
                        "representation": "transfer",
                        "difficulty": "hard",
                        "question": "A taxi service charges $4 base fee plus $2.50 per kilometer. For a trip costing $19, what was the distance in km?",
                        "answer_type": "choice",
                        "options": [
                            "4 + 2.50d = 19, so d = 6 km",
                            "2.50 + 4d = 19, so d = 4.125 km",
                            "4d = 19, so d = 4.75 km",
                            "4 + 2.50d = 19, so d = 9.2 km",
                        ],
                        "answer": "4 + 2.50d = 19, so d = 6 km",
                        "explanation": "2.50d + 4 = 19 => 2.50d = 15 => d = 6 km.",
                        "source_id": "lesson-algebra-04",
                        "concept_id": "ALG-TWOSTEP-01",
                        "misconception_tag": "contextual modeling error",
                    },
                ]

        selected_items = candidate_items[:num_items]
        # If more items requested than available, replicate with unique IDs
        while len(selected_items) < num_items:
            base_item = candidate_items[len(selected_items) % len(candidate_items)].copy()
            base_item["id"] = f"{base_item['id']}-ext-{len(selected_items)}"
            selected_items.append(base_item)

        return {
            "quiz_id": f"quiz-{concept_id.lower()}-01",
            "concept_id": concept_id,
            "target_misconception": misconception,
            "difficulty": difficulty,
            "items": selected_items,
        }
