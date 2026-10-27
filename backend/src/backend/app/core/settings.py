from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AdaptEd API"
    secret_key: str = "change-me-in-production"
    access_token_ttl_seconds: int = 60 * 60 * 24
    teacher_invite_code: str | None = None
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ADAPTED_", extra="ignore")


settings = Settings()
