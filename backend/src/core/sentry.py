"""Sentry integration for error tracking and performance monitoring."""

import logging
from typing import Any, Literal

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from core.config import settings

logger = logging.getLogger(__name__)


def init_sentry(**kwargs: Any) -> None:
    """Initialize Sentry SDK with all integrations.

    This should be called early in the application lifecycle,
    preferably before any other initialization code.
    """
    if not settings.SENTRY_DSN:
        logger.warning("Sentry DSN not configured - error tracking disabled")
        return

    # Configure logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=settings.APP_VERSION,
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="url"),
                RedisIntegration(),
                sentry_logging,
            ],
            # Performance Monitoring
            traces_sample_rate=settings.TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.PROFILES_SAMPLE_RATE,
            # Additional options
            send_default_pii=True,  # Send PII by default
            attach_stacktrace=True,
            max_breadcrumbs=50,
            # Custom tags
        )

        logger.info(
            "Sentry initialized",
            extra={
                "environment": settings.ENVIRONMENT,
                "release": settings.APP_VERSION,
            },
        )

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def capture_exception(error: Exception, **kwargs: Any) -> None:
    """Manually capture an exception and send to Sentry.

    Args:
        error: The exception to capture
        **kwargs: Additional context to attach to the event
    """
    if not settings.SENTRY_DSN:
        logger.error(f"Exception occurred: {error}", exc_info=True)
        return

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_context(key, value)

        sentry_sdk.capture_exception(error)


def capture_message(
    message: str,
    level: Literal["fatal", "critical", "error", "warning", "info", "debug"] = "info",
    **kwargs: Any,
) -> None:
    """Manually capture a message and send to Sentry.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal, critical)
        **kwargs: Additional context to attach to the event
    """
    if not settings.SENTRY_DSN:
        return

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_context(key, value)

        sentry_sdk.capture_message(message, level=level)  # type: ignore[arg-type]


def set_user(user_id: str | None = None, **kwargs: Any) -> None:
    """Set user context for Sentry events.

    Args:
        user_id: Unique identifier for the user
        **kwargs: Additional user attributes (email, username, etc.)
    """
    if not settings.SENTRY_DSN:
        return

    user_data = {"id": user_id} if user_id else {}
    user_data.update(kwargs)

    sentry_sdk.set_user(user_data)


def set_context(key: str, value: dict[str, Any]) -> None:
    """Set additional context for Sentry events.

    Args:
        key: Context key
        value: Context data (must be JSON-serializable)
    """
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.set_context(key, value)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb for debugging context.

    Breadcrumbs are a trail of events that happened prior to an error.

    Args:
        message: Breadcrumb message
        category: Category of the breadcrumb (e.g., "http", "db", "auth")
        level: Severity level
        data: Additional structured data
    """
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


# Transaction helpers for performance monitoring
def start_transaction(
    name: str, op: str = "function"
) -> sentry_sdk.tracing.Transaction | sentry_sdk.tracing.NoOpSpan:
    """Start a performance monitoring transaction.

    Args:
        name: Transaction name (e.g., "scrape_product", "generate_report")
        op: Operation type (e.g., "http", "db", "function")

    Returns:
        Transaction object (use as context manager)
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def start_span(op: str, description: str | None = None) -> sentry_sdk.tracing.Span:
    """Start a performance monitoring span within a transaction.

    Args:
        op: Operation type (e.g., "db.query", "http.client")
        description: Span description

    Returns:
        Span object (use as context manager)
    """
    return sentry_sdk.start_span(op=op, description=description)
