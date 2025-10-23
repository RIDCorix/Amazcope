"""Amazcope ing & Optimization System API.

Main FastAPI application with Tortoise ORM integration,
Prometheus metrics, and comprehensive API routes.
"""

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from api.v1.router import router
from core.config import settings
from core.database import lifespan
from core.sentry import init_sentry
from middleware.rate_limit import RateLimitMiddleware

init_sentry()
# Create FastAPI app with Tortoise ORM lifespan management
app = FastAPI(
    title="Amazcope ing & Optimization System",
    description="AI-powered Amazcopeing with real-time alerts and optimization",
    version=settings.APP_VERSION,
    lifespan=lifespan,  # Tortoise ORM lifecycle management
)

origins = (settings.FRONTEND_URL, settings.HOST_URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

# Prometheus metrics instrumentation
if settings.ENABLE_METRICS:
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    # Expose metrics endpoint
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Include API router
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Amazcopeing & Optimization System API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "amazcope",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
