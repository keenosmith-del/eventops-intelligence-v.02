from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / "backend/.env"), extra="ignore"
    )
    database_url: str = "postgresql+psycopg://eventops:eventops@localhost:5432/eventops"
    mode: str = "fixture"
    environment: str = "local"
    external_calls_enabled: bool = False
    gemini_free_tier_confirmed: bool = False
    google_unbilled_confirmed: bool = False
    directory_zero_cost_confirmed: bool = False
    n8n_zero_cost_confirmed: bool = False
    model_daily_limit: int = Field(default=20, ge=1, le=20)
    http_daily_limit: int = Field(default=100, ge=1, le=100)
    model_operation_limit: int = Field(default=9, ge=1, le=9)
    http_operation_limit: int = Field(default=100, ge=1, le=100)
    max_model_input_chars: int = Field(default=60000, ge=1000, le=60000)
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
    session_hours: int = Field(default=8, ge=1, le=24)

    @property
    def checkpoint_uri(self):
        return self.database_url.replace("postgresql+psycopg://", "postgresql://")


@lru_cache
def settings():
    return validate_configuration(Settings())


def validate_configuration(cfg):
    if cfg.environment not in ("local", "production"):
        raise ValueError("ENVIRONMENT must be local or production")
    if cfg.integration_transport not in ("direct", "n8n"):
        raise ValueError("Invalid integration transport")
    if (
        cfg.gemini_model != "gemini-2.5-flash"
        or cfg.embedding_model != "gemini-embedding-001"
    ):
        raise ValueError("Only audited Gemini models are allowed; no fallback")
    if cfg.environment == "production":
        from urllib.parse import urlparse

        if not cfg.database_url.startswith("postgresql"):
            raise ValueError("Production durable state requires PostgreSQL")
        if not cfg.cookie_secure or urlparse(cfg.frontend_origin).scheme != "https":
            raise ValueError("Production requires HTTPS origin and secure cookies")
        from sqlalchemy.engine import make_url

        database = make_url(cfg.database_url)
        if database.host not in ("localhost", "127.0.0.1") and database.query.get(
            "sslmode"
        ) not in ("require", "verify-full"):
            raise ValueError("Remote production PostgreSQL requires SSL")
    if cfg.mode not in ("live", "fixture"):
        raise ValueError("MODE must be live or fixture")
    if cfg.cookie_samesite not in ("lax", "strict", "none"):
        raise ValueError("Invalid COOKIE_SAMESITE")
    if cfg.cookie_samesite == "none" and not cfg.cookie_secure:
        raise ValueError("Cross-site cookies require COOKIE_SECURE=true")
    if not cfg.database_url.startswith("postgresql") and cfg.mode != "fixture":
        raise ValueError("Live mode requires PostgreSQL")
    return cfg
