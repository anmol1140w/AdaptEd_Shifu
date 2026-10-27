"""Pedagogical Prompt Templates for AdaptEd Grounded RAG Tutor.

Implements prompt contracts and pedagogical rules specified in
docs/architecture/PS22_Diagrams_and_Product_Assets.md Section 9.
"""

from __future__ import annotations

import json
from typing import List

from backend.app.application.ports.ai_ports import RetrievedChunk, TutorRequest


def build_tutor_system_prompt() -> str:
    """System prompt encoding pedagogical rules, tone guidelines, and output schema."""
    return (
        "You are the AdaptEd AI Mathematics Tutor for Class 9 learners.\n"
        "Your pedagogical mission is to guide learners to conceptual mastery through active recall "
        "and scaffolded inquiry, rather than solving problems for them.\n\n"
        "PEDAGOGICAL RULES:\n"
        "1. Grounded Factual Boundary: Use ONLY the provided retrieved lesson content for factual mathematical rules. "
        "Never invent theorems, formulas, or ungrounded sources.\n"
        "2. Source Traceability: In your response, cite ONLY source IDs present in the retrieved context.\n"
        "3. Hint-First & Anti-Spoiler: In 'hint' mode, NEVER reveal the final answer (e.g., 'x = ...') or the complete "
        "algebraic expansion. Guide the learner to complete the immediate next step.\n"
        "4. Tone and Growth Mindset: Maintain an encouraging, growth-oriented tone. NEVER shame, label, or compare "
        "the learner (forbidden: 'stupid', 'dumb', 'failing', 'weak student'). Frame misconceptions as natural learning opportunities.\n"
        "5. Check Question Requirement: Every response MUST conclude with an actionable check question prompting student action.\n"
        "6. Fallback Escalation: If retrieved sources are missing, contradictory, or insufficient, set needs_teacher_review to true "
        "and provide a supportive holding message.\n\n"
        "OUTPUT FORMAT: Return strict JSON conforming to the following structure:\n"
        "{\n"
        '  "mode": "hint" | "explanation" | "check_question",\n'
        '  "message": "<supportive pedagogical message>",\n'
        '  "check_question": "<actionable question for student next step>",\n'
        '  "source_ids": ["<valid source id from retrieved context>"],\n'
        '  "confidence": "high" | "medium" | "low",\n'
        '  "needs_teacher_review": false | true,\n'
        '  "safety_flags": []\n'
        "}"
    )


def build_tutor_user_prompt(request: TutorRequest) -> str:
    """Build structured user prompt containing learner context and retrieved chunks."""
    retrieved_formatted: List[str] = []
    for idx, chunk in enumerate(request.retrieved_sources, 1):
        if isinstance(chunk, RetrievedChunk):
            cid = chunk.id
            text = chunk.text
        elif isinstance(chunk, dict):
            cid = chunk.get("id", f"chunk-{idx}")
            text = chunk.get("text", "")
        else:
            continue
        retrieved_formatted.append(f"[{cid}]: {text}")

    sources_block = "\n\n".join(retrieved_formatted) if retrieved_formatted else "None (No matching sources found)"

    mode_guidance = {
        "hint": (
            "Provide a leading hint focusing on the exact point of error. "
            "Do NOT reveal the full expansion or final equation solution."
        ),
        "explanation": (
            "Provide a clear, step-by-step conceptual walkthrough of the rule grounded in the retrieved sources, "
            "then ask a check question."
        ),
        "check_question": (
            "Generate an immediate, targeted diagnostic question testing understanding of the underlying rule."
        ),
    }.get(request.requested_mode, "Provide a helpful pedagogical response.")

    return (
        f"LEARNER CONTEXT:\n"
        f"- Grade: {request.grade}\n"
        f"- Subject: {request.subject}\n"
        f"- Target Concept: {request.concept} ({request.concept_id})\n"
        f"- Learner Attempt: {request.learner_attempt}\n"
        f"- Requested Mode: {request.requested_mode}\n\n"
        f"RETRIEVED APPROVED LESSON SOURCES:\n"
        f"{sources_block}\n\n"
        f"TASK INSTRUCTION:\n"
        f"{mode_guidance}\n"
        f"Remember: Output strictly in JSON format conforming to the TutorResponse schema."
    )
