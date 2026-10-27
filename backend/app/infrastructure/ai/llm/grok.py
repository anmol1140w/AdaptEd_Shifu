"""Schema-constrained tutor and quiz generation through the xAI Responses API."""

from __future__ import annotations

import json
from typing import Any

import httpx

from ....application.ports.ai import AIIntegrationError
from ..settings import AISettings
from .ollama_cloud import OllamaCloudGenerator

GROK_RESPONSES_URL = "https://api.x.ai/v1/responses"


class GrokGenerator(OllamaCloudGenerator):
    """Generate validated learning drafts with Grok's JSON-schema output mode."""

    provider_name = "Grok"
    provider_id = "grok"
    api_key_setting = "grok_api_key"
    model_setting = "grok_model"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        settings = AISettings()
        key = (api_key or settings.grok_api_key).strip()
        if not key:
            raise ValueError("Set GROK_API_KEY in backend/.env or the process environment")
        super().__init__(api_key=key, model=model or settings.grok_model, timeout_seconds=timeout_seconds)

    def _chat_json(self, *, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                GROK_RESPONSES_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "learning_output",
                            "schema": schema,
                            "strict": True,
                        }
                    },
                    "store": False,
                    "temperature": 0.2,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            body = response.json()
            content = self._response_text(body)
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise TypeError("generated JSON must be an object")
            self._validate_json_schema(parsed, schema)
            return parsed
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, IndexError) as exc:
            raise AIIntegrationError(f"Grok structured generation failed: {exc}") from exc

    @staticmethod
    def _response_text(body: dict[str, Any]) -> str:
        """Extract only the final text payload from an xAI Responses API result."""
        output = body.get("output")
        if not isinstance(output, list):
            raise TypeError("response.output must be an array")
        for item in reversed(output):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content_items = item.get("content")
            if not isinstance(content_items, list):
                continue
            for part in content_items:
                if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
        raise TypeError("response contains no output text")
