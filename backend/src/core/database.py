"""Database configuration and initialization.

This module handles database connection lifecycle for SQLAlchemy 2.0.
Replaces the old Tortoise ORM setup.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings


# Declarative Base for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Async Engine (for FastAPI async endpoints)
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,  # Disable SQL query logging (was: settings.DEBUG)
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync Engine (for Alembic migrations and Dragatiq tasks)
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,  # Disable SQL query logging (was: settings.DEBUG)
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Sync Session Factory
SyncSessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# Dependency for FastAPI (async)
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Context manager for Dramatiq tasks (sync)
def get_sync_db() -> Session:
    """Get sync database session for Dragatiq tasks.

    Usage:
        @dramatiq.actor
        def process_data():
            db = get_sync_db()
            try:
                user = db.query(User).first()
                # ... process
                db.commit()
            finally:
                db.close()
    """
    return SyncSessionLocal()


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for manual database access.

    Usage:
        async with get_async_db_context() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def discover_models() -> None:
    from core.config import CUSTOM_APPS

    for app in CUSTOM_APPS:
        try:
            __import__(app + ".models")
        except ImportError as e:
            print(f"⚠️  Warning: Could not import models from {app}: {e}")


# Initialize database (create tables) - for development only
async def init_db(app: FastAPI | None = None) -> None:
    """Initialize database tables (for development only).

    In production, use Alembic migrations instead.
    """
    discover_models()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Close database connections
async def close_db() -> None:
    """Close all database connections."""
    await async_engine.dispose()
    sync_engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for database connections.

    Usage:
        app = FastAPI(lifespan=lifespan)
    """
    # Startup
    await init_db()  # Only for dev, use Alembic in production
    yield

    # Shutdown
    await close_db()
