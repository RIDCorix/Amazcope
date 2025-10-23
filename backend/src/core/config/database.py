from __future__ import annotations

import time

from pydantic_settings import BaseSettings

from system.checks import BaseCheck, CheckResult


class DatabaseSettings(BaseSettings):
    DATABASE_ENGINE: str = "django.db.backends.postgresql"
    DATABASE_USERNAME: str = "postgres"
    DATABASE_PASSWORD: str = ""
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "postgres"

    TEST_DATABASE_ENGINE: str = DATABASE_ENGINE
    TEST_DATABASE_USERNAME: str = DATABASE_USERNAME
    TEST_DATABASE_PASSWORD: str = DATABASE_PASSWORD
    TEST_DATABASE_HOST: str = DATABASE_HOST
    TEST_DATABASE_PORT: int = DATABASE_PORT
    TEST_DATABASE_NAME: str = DATABASE_NAME

    @property
    def DATABASE_URL(self) -> str:
        return f"postgres://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Synchronous database URL for Alembic and Dragatiq (SQLAlchemy)."""
        return f"postgresql://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Asynchronous database URL for FastAPI (SQLAlchemy with asyncpg)."""
        return f"postgresql+asyncpg://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"


class DatabaseTest(BaseCheck):
    """Test database connectivity."""

    name = "database"

    async def test(self) -> CheckResult:
        """Test database connection using sqlalchemy."""
        start_time = time.time()

        # Attempt to execute a simple query
        from sqlalchemy import text

        from core.database import async_engine

        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        duration_ms = (time.time() - start_time) * 1000
        return CheckResult(
            name=self.name,
            status="success",
            message="Database connection successful",
            details={"database_url": async_engine.url.render_as_string(hide_password=True)},
            duration_ms=duration_ms,
        )
