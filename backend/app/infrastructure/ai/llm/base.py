"""Provider-Neutral LLM Client Base Interface and Common Types."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, TypeVar

from backend.app.application.ports.ai_ports import BaseSchema, LLMPort

T = TypeVar("T", bound=BaseSchema)


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider encounters network, authentication, or generation errors."""

    def __init__(self, message: str, provider: str = "unknown", status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


@dataclass
class LLMResponse:
    """Standardized response container returned by LLM adapters."""

    text: str
    raw_response: Optional[Any] = None
    model: str = "mock-model"
    total_tokens: int = 0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLMClient(LLMPort, ABC):
    """Abstract base class for provider-neutral LLM adapters."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Generate unstructured text completion."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured completion adhering to schema type."""
        pass

    @staticmethod
    def _extract_json_block(text: str) -> str:
        """Extract JSON substring from potential markdown code fences."""
        cleaned = text.strip()
        if "```json" in cleaned:
            parts = cleaned.split("```json")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()
        elif "```" in cleaned:
            parts = cleaned.split("```")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()
        return cleaned
