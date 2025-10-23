from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request supporting email or username."""

    email_or_username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    id: UUID
    username: str
    full_name: str
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False

    # User settings (if populated)
    email_notifications_enabled: bool | None = None
    price_alert_emails: bool | None = None
    bsr_alert_emails: bool | None = None
    stock_alert_emails: bool | None = None
    daily_summary_emails: bool | None = None
    weekly_report_emails: bool | None = None
    default_price_threshold: float | None = None
    default_bsr_threshold: float | None = None
    theme: str | None = None
    language: str | None = None
    timezone: str | None = None
    date_format: str | None = None
    currency_display: str | None = None
    products_per_page: int | None = None
    default_sort_by: str | None = None
    default_sort_order: str | None = None
    show_inactive_products: bool | None = None
    auto_refresh_dashboard: bool | None = None
    refresh_interval_minutes: int | None = None
    share_analytics: bool | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Any  # UserOut


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str


class UserUpdate(BaseModel):
    """Schema for updating user information (all fields optional)."""

    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings (all fields optional)."""

    # Notification Settings
    email_notifications_enabled: bool | None = None
    price_alert_emails: bool | None = None
    bsr_alert_emails: bool | None = None
    stock_alert_emails: bool | None = None
    daily_summary_emails: bool | None = None
    weekly_report_emails: bool | None = None

    # Alert Thresholds
    default_price_threshold: float | None = Field(None, ge=0, le=100)
    default_bsr_threshold: float | None = Field(None, ge=0, le=100)

    # Display Preferences
    theme: str | None = Field(None, pattern="^(light|dark|auto)$")
    language: str | None = Field(None, min_length=2, max_length=10)
    timezone: str | None = Field(None, max_length=50)
    date_format: str | None = Field(None, max_length=20)
    currency_display: str | None = Field(None, min_length=3, max_length=10)

    # Dashboard Preferences
    products_per_page: int | None = Field(None, ge=10, le=100)
    default_sort_by: str | None = Field(None, max_length=50)
    default_sort_order: str | None = Field(None, pattern="^(asc|desc)$")
    show_inactive_products: bool | None = None

    # Data Refresh Settings
    auto_refresh_dashboard: bool | None = None
    refresh_interval_minutes: int | None = Field(None, ge=1, le=60)

    # Privacy Settings
    share_analytics: bool | None = None


# Generate Pydantic schemas from Tortoise ORM model
# This enables from_tortoise_orm functionality
class UserSettingsOut(BaseModel):
    # Notification Settings
    email_notifications_enabled: bool = True
    price_alert_emails: bool = True
    bsr_alert_emails: bool = True
    stock_alert_emails: bool = True
    daily_summary_emails: bool = False
    weekly_report_emails: bool = False

    # Alert Thresholds (global defaults)
    default_price_threshold: float = 10.0  # Percentage
    default_bsr_threshold: float = 30.0  # Percentage

    # Display Preferences
    theme: str = "light"  # light, dark, auto
    language: str = "en"  # en, zh, es, etc.
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    currency_display: str = "USD"

    # Dashboard Preferences
    products_per_page: int = 20
    default_sort_by: str = "created_at"  # created_at, title, price
    default_sort_order: str = "desc"  # asc, desc
    show_inactive_products: bool = False

    # Data Refresh Settings
    auto_refresh_dashboard: bool | None = True
    refresh_interval_minutes: int | None = 5

    # Privacy Settings
    share_analytics: bool | None = False

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
