"""Application configuration settings."""

from typing import Self
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application-level configuration."""

    APP_NAME: str = "Amazcope"

    # Monitoring
    ENABLE_METRICS: bool = True

    TIMEZONE_NAME: str = "Asia/Taipei"

    @property
    def TIMEZONE(self: Self) -> ZoneInfo:
        return ZoneInfo(self.TIMEZONE_NAME)

    SECRET_KEY: str | None = None
    ENVIRONMENT: str = "local"
    HOST_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    DISABLE_RATE_LIMITING: bool = False

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
