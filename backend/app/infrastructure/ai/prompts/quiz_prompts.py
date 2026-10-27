"""Prompt Templates for Targeted Weak-Area Quiz Generation.

Implements multi-representation item generation (symbolic, error analysis,
verbal/visual, and transfer) targeting diagnosed learner misconceptions.
"""

from __future__ import annotations

from typing import List

from backend.app.application.ports.ai_ports import QuizRequest


def build_quiz_system_prompt() -> str:
    """System prompt enforcing multi-representation diversity and rubric clarity."""
    return (
        "You are the AdaptEd Assessment Item Specialist for Class 9 Mathematics.\n"
        "Your task is to generate diagnostic assessment items tailored to address a learner's specific misconception.\n\n"
        "REPRESENTATION REQUIREMENTS:\n"
        "Items must vary representation across:\n"
        "1. symbolic: Direct algebraic equation or expression manipulation.\n"
        "2. error_analysis: Diagnostic evaluation of a flawed student attempt.\n"
        "3. verbal: Natural language conceptual justification or visual/geometric interpretation.\n"
        "4. transfer: Contextual word problem, multi-step bracket solving, or real-world application.\n\n"
        "QUALITY CONSTRAINTS:\n"
        "- Choice items MUST include plausible distractors derived from common algebra misconceptions.\n"
        "- All items must include clear step-by-step explanations.\n"
        "- Output strictly in JSON conforming to the QuizResponse schema."
    )


def build_quiz_user_prompt(request: QuizRequest) -> str:
    """Build user prompt for quiz generation."""
    reps = request.requested_representations or ["symbolic", "error_analysis", "verbal", "transfer"]
    reps_str = ", ".join(reps)

    return (
        f"QUIZ GENERATION REQUEST:\n"
        f"- Learner ID: {request.learner_id}\n"
        f"- Grade: {request.grade}\n"
        f"- Subject: {request.subject}\n"
        f"- Concept ID: {request.concept_id}\n"
        f"- Target Misconception: {request.misconception}\n"
        f"- Target Difficulty: {request.difficulty}\n"
        f"- Item Count: {request.num_items}\n"
        f"- Required Representations: {reps_str}\n\n"
        f"Generate {request.num_items} structured assessment items addressing this misconception. "
        f"Ensure representation diversity and return strict JSON conforming to QuizResponse."
    )
