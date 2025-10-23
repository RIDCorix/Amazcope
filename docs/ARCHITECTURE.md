# Amazcope Architecture

This document describes the architecture of Amazcope as of Oct 23, 2025. It summarizes components, data flow, key design decisions, deployment topology, and integration points. It is intended for developers, SREs, and architects who need a high level and mid-level view of how the system is built and how components interact.

## High-level Overview

Amazcope is a service-oriented product-tracking and optimization platform focused on Amazon marketplace monitoring. The main runtime components are:

- API service: FastAPI application implementing REST endpoints, authentication, and admin operations.
- Background workers: Dragatiq workers (and APScheduler) executing scraping, monitoring, alerts, and AI/reporting jobs.
- Database: PostgreSQL (managed, e.g., Supabase or RDS) for primary storage.
- Cache/Queue: Redis used both as Dragatiq broker/result backend and as caching store.
- External integrations: Apify for Amazon scraping, OpenAI for optimization/suggestion generation, optional Apify proxies.
- MCP Server: `mcp_server` exposes a Model Context Protocol (agent-facing) interface enabling automation agents to call tools/resources.
- Observability: Prometheus metrics, Grafana dashboards, and Sentry for error tracking.

The system is designed to be modular: API services handle request/response concerns and orchestration, while long-running or IO-heavy tasks are delegated to Dragatiq workers.

## Technology Stack

- Python 3.11+ with FastAPI (async-first)
- SQLAlchemy 2.0 (async + sync engines)
- Pydantic / pydantic-settings for config and validation
- Dragatiq 1.18 for background tasks
- Redis for Dragatiq broker/result backend and caching
- PostgreSQL for relational data
- OpenAI (Async client) for text generation + suggestion models
- Apify client for web scraping actors
- GitHub Actions CI, Docker multi-stage builds
- Terraform (in `deployment/terraform`) for infra provisioning
- Zeabur / Docker Compose deploy options

## Core Components

### API Service (`backend/src/main.py`)
- FastAPI application with middleware for CORS, rate limiting (`RateLimitMiddleware`), request logging, and Prometheus instrumentation.
- Route structure is mounted under `backend/src/api/v1/` and grouped into logical routers (auth, users, tracking, suggestions, metrics, notifications, user-products, user-settings, chat).
- Dependency injection used for DB sessions (`get_async_db`) and auth (`get_current_user`).
- Uses SQLAlchemy 2.0 async engine for request handling.

### Database Layer (`backend/src/core/database.py` and `backend/src/core/config/database.py`)
- Dual-engine pattern: async engine for FastAPI requests and async sessions; sync engine for Dragatiq tasks and migration tooling.
- Session factories: `AsyncSessionLocal` for API and `SyncSessionLocal` for workers/migrations.
- Connection pooling and timeouts configured for production readiness.

### Models (`backend/src/products/models.py`, `backend/src/users/models.py`, `backend/src/optimization/models.py`)
- Declarative SQLAlchemy models using `Mapped[...]` and `mapped_column`.
- Core entities: `Product`, `ProductSnapshot`, `Review`, `UserProduct`, `Suggestion`, `SuggestionAction`, `Alert`.
- Snapshots store time-series data (price, BSR, ratings) with indexes for efficient historical queries.

### Background Workers & Tasks (`backend/src/core/celery.py`, `backend/src/tasks/`, `backend/src/products/tasks.py`)
- Dragatiq is configured with Redis broker/result backend.
- APScheduler schedule includes daily product updates, snapshot cleanup, and AI suggestion generation.
- Tasks perform scraping orchestration (via Apify), change detection, alerting, and persistence of snapshot data.

### Scraping & External Integrations (`backend/src/services/apify_service.py`, `backend/src/scrapper/`)
- `ApifyService` calls Apify actors for product details, reviews, and bestsellers.
- Scraped items are validated with Pydantic models in `schemas/` and normalized to domain models.
- Error handling marks 404/unlisted items and optionally flags `is_unlisted` on products.

### Optimization & AI (`backend/src/services/optimization_service.py`, `backend/src/optimization/`)
- `OptimizationService` orchestrates data preparation, caching, calling OpenAI Async client, and persisting suggestions.
- Reports (`OptimizationReport`) are created and cached to limit API/OpenAI usage.

### MCP Server (`backend/src/mcp_server/`)
- The MCP server exposes tools and resources via FastMCP to enable programmatic agents to query and act on product data.
- Tools wrap DB access and domain operations (e.g., `get_product_details`, `search_products`) and are implemented as async functions decorated with `@mcp_server.tool()`.

## Data Flow (Typical)

1. User imports a product (UI → API). API validates and enqueues a scraping job (Dragatiq) to Apify.
2. Dragatiq worker invokes `ApifyService` to fetch product details. Results are normalized and persisted as `Product` and `ProductSnapshot` rows.
3. Daily/periodic tasks run via APScheduler to re-scrape products, compute trends in `metrics_service`, and generate `Suggestion` objects using `OptimizationService`.
4. Users view dashboards and suggestions; accepting a suggestion can create `SuggestionAction` which Dragatiq may apply.
5. MCP Server tools allow automation agents to query product states and trigger actions programmatically.

## API and Authentication

- JWT-based authentication with short-lived access tokens and refresh tokens.
- Endpoints are grouped by feature area; most endpoints require authorization.
- Rate limiting middleware enforces stricter limits on auth endpoints (login/register) and reasonable defaults for others.

## Observability and Monitoring

- Prometheus instrumentation using FastAPI instrumentator; metrics exposed at `/metrics`.
- Grafana dashboards in `/backend/grafana/provisioning` for product metrics, worker task rates, and system health.
- Sentry integrated for error tracking; initialized early in Dragatiq and FastAPI processes.

## Deployment & Infrastructure

- Docker multi-stage builds produce `backend` image for `api`, `worker` and `scheduler`. Docker Compose used for local dev. CI builds images via GitHub Actions and pushes to Amazon ECR.
- Terraform configurations in `deployment/terraform` can provision AWS infrastructure (RDS, ElastiCache, ECS, ALB).

## Notable Design Decisions & Migration Notes

- Migration from Tortoise ORM to SQLAlchemy 2.0: codebase now uses `Mapped[...]` types and `mapped_column`. Some legacy code sections still reference older ORM patterns; these were updated incrementally.
- FastAPI uses folder-by-feature structure under `api/v1/` for better modularity.
- MCP server adds a distinct automation surface; tools use the same DB layer but are explicitly separated to control surface area.

## Directory Map

- `backend/src/api/v1/` — REST endpoints
- `backend/src/core/` — config, database, celery init, sentry, security utilities
- `backend/src/services/` — Apify, OpenAI, caching, metrics
- `backend/src/products/` — product models, tasks, domain logic
- `backend/src/optimization/` — suggestion models and logic
- `backend/src/mcp_server/` — MCP server tools and resources
