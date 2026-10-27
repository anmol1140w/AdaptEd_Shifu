"""Configuration shared by AI infrastructure adapters."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[3]


class AISettings(BaseSettings):
    """Load AI service settings from process environment or backend/.env."""

    model_config = SettingsConfigDict(env_file=BACKEND_ROOT / ".env", extra="ignore")

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_read_only_api_key: str = ""
    grok_api_key: str = ""
    grok_model: str = "grok-4.7"
    ollama_api_key: str = ""
    ollama_model: str = "gemma4:31b"
