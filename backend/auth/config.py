"""
Application settings for authentication
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Application configuration
    APP_NAME: str = "TP_Agile Auth Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database configuration (for future use)
    DATABASE_URL: str = "sqlite:///./data/auth.db"


settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
