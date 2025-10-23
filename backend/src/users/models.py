"""User models using SQLAlchemy."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BaseModel
from notification.models import Notification
from products.models import UserProduct

if TYPE_CHECKING:
    from alert.models import Alert


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="User email address",
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="Username"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Hashed password"
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Full name")

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Is account active"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Has superuser privileges"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Email verified"
    )

    # Login security tracking
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Failed login attempt count"
    )
    account_locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Account lock expiration"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last successful login"
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="Last login IP (IPv6 supported)"
    )
    last_failed_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last failed login attempt"
    )

    # Relationships
    settings: Mapped[UserSettings | None] = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    user_products: Mapped[list[UserProduct]] = relationship(
        UserProduct, back_populates="user", cascade="all, delete-orphan"
    )
    alerts: Mapped[list[Alert]] = relationship(
        "Alert", back_populates="user", cascade="all, delete-orphan"
    )

    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class UserSettings(BaseModel):
    """User settings and preferences.

    Stores user-specific configuration for notifications, display preferences,
    and other customizable options.
    """

    __tablename__ = "user_settings"

    # User relationship (one-to-one)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="User ID",
    )

    # Notification Settings
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    price_alert_emails: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bsr_alert_emails: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stock_alert_emails: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_summary_emails: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weekly_report_emails: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Alert Thresholds (global defaults)
    default_price_threshold: Mapped[float] = mapped_column(
        Float,
        default=10.0,
        nullable=False,
        comment="Default price change threshold (%)",
    )
    default_bsr_threshold: Mapped[float] = mapped_column(
        Float, default=30.0, nullable=False, comment="Default BSR change threshold (%)"
    )

    # Display Preferences
    theme: Mapped[str] = mapped_column(
        String(20),
        default="light",
        nullable=False,
        comment="UI theme: light, dark, auto",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
        comment="Language code (en, zh, es, etc.)",
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    date_format: Mapped[str] = mapped_column(String(20), default="YYYY-MM-DD", nullable=False)
    currency_display: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    # Dashboard Preferences
    products_per_page: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    default_sort_by: Mapped[str] = mapped_column(
        String(50), default="created_at", nullable=False, comment="Default sort field"
    )
    default_sort_order: Mapped[str] = mapped_column(
        String(10), default="desc", nullable=False, comment="asc or desc"
    )
    show_inactive_products: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Data Refresh Settings
    auto_refresh_dashboard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    refresh_interval_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Privacy Settings
    share_analytics: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id})>"
