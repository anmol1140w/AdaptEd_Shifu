from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AdaptEd API"
    secret_key: str = "change-me-in-production"
    access_token_ttl_seconds: int = 60 * 60 * 24
    teacher_invite_code: str | None = None
    database_path: str = str(Path(__file__).resolve().parents[5] / "data" / "adapted.sqlite3")
    database_url: str = "postgresql://adapted_user@127.0.0.1:5432/adapted"
    database_password: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8000/api/v1/auth/google/callback"
    frontend_url: str = "http://127.0.0.1:5173"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    database_url: str = "postgresql://adapted_user@127.0.0.1:5432/adapted"
    database_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ADAPTED_", extra="ignore")


settings = Settings()
