"""AI Prompts Package."""

from backend.app.infrastructure.ai.prompts.quiz_prompts import (
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from backend.app.infrastructure.ai.prompts.tutor_prompts import (
    build_tutor_system_prompt,
    build_tutor_user_prompt,
)

__all__ = [
    "build_tutor_system_prompt",
    "build_tutor_user_prompt",
    "build_quiz_system_prompt",
    "build_quiz_user_prompt",
]
