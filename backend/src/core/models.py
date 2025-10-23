"""Base models for SQLAlchemy.

Provides base classes with common fields like id, created_at, updated_at.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declarative_mixin, declared_attr, mapped_column

from core.database import Base
from core.utils import now


@declarative_mixin
class TimestampMixin:
    """Mixin for automatic timestamp fields."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:  # noqa: N805
        """Timestamp when record was created."""
        return mapped_column(
            DateTime(timezone=True),
            default=now,
            nullable=False,
            comment="Record creation timestamp",
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:  # noqa: N805
        """Timestamp when record was last updated."""
        return mapped_column(
            DateTime(timezone=True),
            default=now,
            nullable=False,
            comment="Record last update timestamp",
        )


class BaseModel(Base, TimestampMixin):
    """Abstract base model with ID and timestamps.

    All models should inherit from this to get:
    - id: Primary key (UUID v4)
    - created_at: Auto-generated creation timestamp
    - updated_at: Auto-updated modification timestamp
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key (UUID v4)",
    )

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def as_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Choices(str):
    @classmethod
    def choices(cls) -> SQLEnum:
        """Convert enum to SQLAlchemy Enum."""
        return SQLEnum(
            *[v for k, v in vars(cls).items() if not k.startswith("__") and not callable(v)],
            name=cls.__name__.lower(),
        )
