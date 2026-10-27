"""Runtime AI settings for the packaged FastAPI application."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[5]


class AISettings(BaseSettings):
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_read_only_api_key: str = ""
    ollama_api_key: str = ""
    ollama_model: str = "gemma4:31b"

    model_config = SettingsConfigDict(env_file=BACKEND_ROOT / ".env", extra="ignore")
