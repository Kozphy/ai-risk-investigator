from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Risk Investigator"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: str = "postgresql+asyncpg://risk:risk@localhost:5432/ai_risk_investigator"
    database_url_sync: str = "postgresql://risk:risk@localhost:5432/ai_risk_investigator"

    jwt_secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    default_llm_provider: Literal["openai", "anthropic", "mock"] = "mock"
    openai_model: str = "gpt-4.1"
    anthropic_model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072
    llm_temperature: float = 0.1
    max_analysis_tokens: int = 8000

    upload_dir: str = "/data/uploads"
    knowledge_dir: str = "/data/knowledge"
    report_dir: str = "/data/reports"
    max_upload_bytes: int = 25 * 1024 * 1024
    allowed_extensions: list[str] = Field(default_factory=lambda: [".pdf", ".docx", ".txt"])

    rate_limit: str = "60/minute"
    otel_exporter_otlp_endpoint: str | None = None
    sentry_dsn: str | None = None
    log_level: str = "INFO"
    demo_mode: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
