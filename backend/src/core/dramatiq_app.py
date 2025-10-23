"""Dramatiq task queue configuration."""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import (
    AgeLimit,
    AsyncIO,
    Callbacks,
    Pipelines,
    Prometheus,
    Retries,
    ShutdownNotifications,
    TimeLimit,
)
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

from core.config import CUSTOM_APPS, settings
from core.database import discover_models
from core.sentry import init_sentry

# Initialize Sentry for error tracking
init_sentry()

result_backend = RedisBackend(url=settings.REDIS_URL)
broker = RedisBroker(
    url=settings.REDIS_URL,
    middleware=[
        Prometheus(),
        AgeLimit(),
        TimeLimit(),
        Callbacks(),
        Pipelines(),
        Retries(min_backoff=1000, max_backoff=900000, max_retries=3),
        ShutdownNotifications(),
    ],
)
broker.add_middleware(Results(backend=result_backend))
broker.add_middleware(AsyncIO())
# Configure Redis broker

# Set the default broker
dramatiq.set_broker(broker)

# Discover database models
discover_models()

# Auto-discover actors from registered apps
# This will import all tasks modules to register their actors
for app in CUSTOM_APPS:
    try:
        __import__(f"{app}.tasks")
    except ImportError:
        pass  # Module doesn't have tasks, skip

print(f"Dramatiq broker initialized with Redis URL: {settings.REDIS_URL}")
