from __future__ import annotations

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from .ai import AISettings
from .apify import ApifyConfig
from .app import AppConfig
from .database import DatabaseSettings
from .dramatiq import DramatiqSettings
from .email import EmailSettings
from .frontend import FrontendRedirectSettings
from .redis import CacheSettings
from .sentry import SentrySettings


class Settings(
    FrontendRedirectSettings,
    DatabaseSettings,
    SentrySettings,
    CacheSettings,
    ApifyConfig,
    EmailSettings,
    AISettings,
    AppConfig,
    DramatiqSettings,
):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


load_dotenv()  # Load environment variables from .env file

settings = Settings()
CUSTOM_APPS = [
    "users",
    "optimization",
    "products",
    "notification",
    "alert",
    "system",
]
