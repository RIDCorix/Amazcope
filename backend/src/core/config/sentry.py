from pydantic_settings import BaseSettings


class SentrySettings(BaseSettings):
    SENTRY_DSN: str | None = None
    TRACES_SAMPLE_RATE: float = 1.0
    PROFILES_SAMPLE_RATE: float = 1.0
