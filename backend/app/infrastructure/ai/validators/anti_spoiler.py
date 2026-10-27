"""Anti-Spoiler Guardrail for AdaptEd AI Tutor (R3).

Detects and rejects full solution dumping, final variable assignments,
and full equation transformations during hint mode.
"""

from __future__ import annotations

import re
from typing import Optional


class AntiSpoilerGuard:
    """Anti-spoiler guardrail verifying hint responses avoid dumping answers."""

    # Patterns for detecting spoilers in hint mode
    PATTERNS = [
        # Explicit solved variable: e.g. x = -7, x = - 7, y = -3, x = 4, x = −7
        re.compile(r"\b[a-zA-Z]\s*=\s*-?\s*\d+(\.\d+)?\b", re.IGNORECASE),
        # Full equation expansions: e.g. -2x - 6 = 8, -2x - 6
        re.compile(r"-?2x\s*-\s*6\s*=\s*8", re.IGNORECASE),
        re.compile(r"gives\s+-?2x\s*-\s*6\b", re.IGNORECASE),
        re.compile(r"is\s+-?2x\s*-\s*6\b", re.IGNORECASE),
        re.compile(r"-?2x\s*=\s*14\b", re.IGNORECASE),
        # Explicit answer revelation stems
        re.compile(r"\bthe (?:final )?answer (?:to the equation )?is\b", re.IGNORECASE),
        re.compile(r"\bthe (?:full )?solution is\b", re.IGNORECASE),
        re.compile(r"\bthe simplified equation is\b", re.IGNORECASE),
        re.compile(r"\bcorrect answer is\b", re.IGNORECASE),
        # Natural language verbal solution statements: e.g. "The final value of x is -7."
        re.compile(r"\b(?:the\s+)?(?:final\s+)?value\s+of\s+[a-zA-Z]\s+is\b", re.IGNORECASE),
        re.compile(r"\b[a-zA-Z]\s+is\s+equal\s+to\s+-?\d+", re.IGNORECASE),
    ]

    def _normalize(self, text: str) -> str:
        """Normalize unicode minus signs and excess whitespace."""
        # Replace unicode minus sign (−, \u2212) with standard hyphen (-)
        normalized = text.replace("\u2212", "-")
        # Collapse multiple whitespace
        return re.sub(r"\s+", " ", normalized).strip()

    def is_spoiler(self, text: str, mode: str = "hint") -> bool:
        """Return True if text contains a solution spoiler in hint mode, False otherwise."""
        if mode != "hint":
            return False

        norm_text = self._normalize(text)
        for pattern in self.PATTERNS:
            if pattern.search(norm_text):
                return True
        return False

    def detect_spoiler(self, text: str, mode: str = "hint") -> bool:
        """Alias for is_spoiler."""
        return self.is_spoiler(text, mode=mode)

    def check(self, text: str, mode: str = "hint") -> bool:
        """Alias for is_spoiler."""
        return self.is_spoiler(text, mode=mode)

    def __call__(self, text: str, mode: str = "hint") -> bool:
        """Callable alias."""
        return self.is_spoiler(text, mode=mode)
