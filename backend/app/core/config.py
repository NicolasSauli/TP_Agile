from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or ``.env``."""

    app_name: str = "Scrum AI API"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    database_url: str = f"sqlite:///{BACKEND_DIRECTORY / 'scrum_ai.db'}"
    gemini_api_key: str | None = None
    agent_model: str = "gemini-2.5-flash"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Keep comma-separated values from .env as strings so the validator
        # below can turn CORS_ORIGINS into a list. Pydantic otherwise expects
        # a JSON array before field validation runs.
        enable_decoding=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
