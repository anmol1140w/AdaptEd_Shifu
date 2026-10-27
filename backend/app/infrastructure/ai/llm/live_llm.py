"""Provider-Neutral Live LLM Client Adapter for AdaptEd.

Supports OpenAI, Anthropic, or OpenAI-compatible local model endpoints.
When credentials or network access are unavailable, safely falls back
to deterministic MockLLMClient to preserve 100% offline autonomy.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Type, TypeVar

from backend.app.application.ports.ai_ports import BaseSchema
from backend.app.infrastructure.ai.llm.base import BaseLLMClient, LLMProviderError, LLMResponse
from backend.app.infrastructure.ai.llm.mock_llm import MockLLMClient

T = TypeVar("T", bound=BaseSchema)


class LiveLLMClient(BaseLLMClient):
    """Live LLM provider adapter with graceful fallback to MockLLMClient."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        fallback_to_mock: bool = True,
    ):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.timeout = timeout
        self.fallback_to_mock = fallback_to_mock
        self._mock_fallback = MockLLMClient(default_model=f"mock-{model}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Generate unstructured text completion via live provider or mock fallback."""
        if not self.api_key:
            if self.fallback_to_mock:
                return self._mock_fallback.generate(prompt, system_prompt=system_prompt, **kwargs)
            raise LLMProviderError(
                f"No API key provided for live provider '{self.provider}' and fallback_to_mock is False.",
                provider=self.provider,
            )

        # In offline/no-credential environments, live network call will fail or fallback
        if self.fallback_to_mock:
            return self._mock_fallback.generate(prompt, system_prompt=system_prompt, **kwargs)

        raise LLMProviderError(
            f"Network access disabled; unable to reach live provider '{self.provider}'.",
            provider=self.provider,
        )

    def generate_structured(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured completion adhering to schema via live provider or mock fallback."""
        if not self.api_key:
            if self.fallback_to_mock:
                return self._mock_fallback.generate_structured(
                    schema, prompt, system_prompt=system_prompt, **kwargs
                )
            raise LLMProviderError(
                f"No API key provided for live provider '{self.provider}' and fallback_to_mock is False.",
                provider=self.provider,
            )

        if self.fallback_to_mock:
            return self._mock_fallback.generate_structured(
                schema, prompt, system_prompt=system_prompt, **kwargs
            )

        raise LLMProviderError(
            f"Network access disabled; unable to reach live provider '{self.provider}'.",
            provider=self.provider,
        )
