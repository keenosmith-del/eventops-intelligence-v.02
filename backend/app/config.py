from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / "backend/.env"), extra="ignore"
    )
    database_url: str = "postgresql+psycopg://eventops:eventops@localhost:5432/eventops"
    mode: str = "live"
    demo_username: str = "operator"
    demo_password: str = ""
    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:5050/api/integrations/google/callback"
    token_encryption_key: str = ""
    calendar_id: str = "primary"
    directory_url: str = ""
    integration_transport: str = "direct"
    n8n_base_url: str = "http://localhost:5678"
    n8n_webhook_secret: str = ""
    worker_enabled: bool = True
    session_hours: int = 8

    @property
    def checkpoint_uri(self):
        return self.database_url.replace("postgresql+psycopg://", "postgresql://")


@lru_cache
def settings():
    cfg = Settings()
    if cfg.mode not in ("live", "fixture"):
        raise ValueError("MODE must be live or fixture")
    if cfg.cookie_samesite not in ("lax", "strict", "none"):
        raise ValueError("Invalid COOKIE_SAMESITE")
    if cfg.cookie_samesite == "none" and not cfg.cookie_secure:
        raise ValueError("Cross-site cookies require COOKIE_SECURE=true")
    if not cfg.database_url.startswith("postgresql") and cfg.mode != "fixture":
        raise ValueError("Live mode requires PostgreSQL")
    return cfg
