# Amazcope Design Decisions

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture Decisions](#architecture-decisions)

---

## Overview

Amazcope is a production-ready Amazon product tracking and optimization system designed for:
- **Real-time monitoring**: Price, BSR, inventory, and competitor tracking
- **AI-powered optimization**: OpenAI-driven listing improvement suggestions
- **Multi-tenancy**: User-based product ownership and access control
- **Scalability**: Handle thousands of products with background processing
- **Developer experience**: Modern tooling and clear patterns

This document explains **why** I made specific technical decisions and the **trade-offs** involved.

---

## Architecture Decisions

### ADR-001: Microservices vs Monolith

**Decision**: Modular Monolith (initial), with service-oriented architecture internally

**Context**:
- Early-stage product with evolving requirements
- Small team (1-3 developers initially)
- Need rapid iteration and deployment

**Rationale**:
- **Monolith Advantages**:
  - Simpler deployment (single Docker image)
  - Easier debugging and local development
  - Shared database transactions
  - Lower operational complexity

- **Service-Oriented Internally**:
  - Clear module boundaries (products, users, notifications, etc.)
  - Easy to extract microservices later if needed
  - Repository pattern for data access
  - Service layer for business logic

**Trade-offs**:
-  Faster initial development
-  Lower infrastructure costs
-  Shared database (potential bottleneck)

**Future Path**:
- Extract high-load services (scraping, AI processing) to microservices as needed
- Use message queues (already in place with Dramatiq) for async communication

### ADR-002: Async Python vs Sync

**Decision**: Async Python with FastAPI and SQLAlchemy async

**Rationale**:
- **I/O-bound workload**: Heavy external API calls (Apify, OpenAI, Amazon)
- **High concurrency**: Handle thousands of products with minimal resources
- **Modern FastAPI**: Built for async, excellent performance
- **Database efficiency**: Non-blocking DB queries with asyncpg

**Implementation**:
```python
# All API endpoints use async/await
@router.get("/products/{product_id}")
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()
```

**Trade-offs**:
-  10-100x better I/O concurrency
-  Lower memory footprint per request
-  Better for real-time features
-  More complex debugging (async stack traces)
-  All dependencies must support async

**Alternatives Considered**:
- **Sync Flask/Django**: Easier but worse performance for I/O-bound tasks
- **Go/Node.js**: Excellent performance but Python has better AI/ML ecosystem

### ADR-003: UUID vs Integer IDs

**Decision**: UUIDs for all primary keys

**Rationale**:
- **Security**: No sequential ID guessing
- **Distributed systems**: Generate IDs without coordination
- **Multi-tenancy**: Prevent user enumeration
- **Merging data**: Safe to merge databases (no ID conflicts)

**Implementation**:
```python
class BaseModel:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()")
    )
```

**Trade-offs**:
-  Better security (no enumeration attacks)
-  Distributed-friendly
-  No coordination needed
-  Larger index size (16 bytes vs 4-8 bytes)
-  Less human-readable in logs
-  Slightly slower joins (marginal)

**Migration Story**:
- Started with integer IDs
- Migrated to UUIDs in October 2025 (see `alembic/versions/fd2c4d97639a_convert_integer_ids_to_uuid.py`)
- Used dual-column approach during migration

---

### ADR-004: Next.js to Vite Migration

**Decision**: Migrate from Next.js to Vite + React for frontend build tooling

**Context**:
- Initial frontend built with Next.js 14 (App Router)
- Deployment costs on Vercel/Next.js-optimized platforms were higher than expected
- Server-Side Rendering (SSR) features were underutilized (most pages are client-side)
- Build times were slower than desired for rapid iteration

**Rationale**:

**Cost Reduction**:
- **Next.js**: Requires Node.js runtime on server, uses serverless functions, higher hosting costs
- **Vite**: Static build output, can deploy to any static hosting (Netlify, Cloudflare Pages, S3)
- **Savings**: ~70% reduction in hosting costs ($50/month → $15/month)

**Build Performance**:
- **Next.js**: Build time ~2-3 minutes for medium-sized app
- **Vite**: Build time ~30-60 seconds (3-5x faster)
- **Hot Module Replacement (HMR)**: Vite's HMR is near-instantaneous vs Next.js's slower reloads

**Simplicity**:
- **Next.js**: Server components, app router, API routes (complexity I didn't need)
- **Vite**: Simple SPA, all API calls go to FastAPI backend
- **Learning curve**: Vite is simpler for team members familiar with Create React App

**Implementation**:

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

**Migration Strategy**:

1. **Phase 1 - Setup Vite**:
   ```bash
   npm create vite@latest frontend -- --template react-ts
   ```

2. **Phase 2 - Migrate Components**:
   - Copied `src/components/` directory unchanged
   - Converted App Router pages to React Router routes
   - No component code changes needed (both use React 18)

3. **Phase 3 - Update Routing**:
   ```typescript
   // Before (Next.js App Router)
   // app/dashboard/page.tsx
   export default function DashboardPage() { ... }

   // After (React Router)
   // src/pages/Dashboard.tsx
   import { useNavigate } from 'react-router-dom';
   export function DashboardPage() { ... }
   ```

4. **Phase 4 - Environment Variables**:
   ```bash
   # Next.js: NEXT_PUBLIC_API_URL
   # Vite: VITE_API_URL
   ```

5. **Phase 5 - Build & Deploy**:
   ```dockerfile
   # Simplified Dockerfile (static build)
   FROM node:18-alpine AS build
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   FROM nginx:alpine
   COPY --from=build /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/nginx.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

**Trade-offs**:

 **Pros**:
- **Cost**: 70% reduction in hosting costs
- **Speed**: 3-5x faster builds, instant HMR
- **Simplicity**: Easier to understand and maintain
- **Flexibility**: Deploy anywhere (S3, Netlify, Cloudflare, Nginx)
- **Bundle size**: Better tree-shaking, smaller bundles

 **Cons**:
- **No SSR**: Lost server-side rendering (not needed for our use case)
- **No API routes**: Must use separate FastAPI backend (already doing this)
- **SEO**: Requires client-side rendering workarounds (not critical for B2B SaaS)
- **Initial load**: Slightly slower first page load vs SSR (acceptable trade-off)

**Conclusion**: Vite was the right choice for our product-market fit and cost constraints.

---

### ADR-005: Tortoise ORM to SQLAlchemy Migration

**Decision**: Migrate from Tortoise ORM to SQLAlchemy 2.0 (async)

**Context**:
- Initial backend built with Tortoise ORM (async-native ORM for Python)
- As project matured, encountered limitations in ecosystem support and advanced features
- SQLAlchemy 2.0 released with full async support, addressing previous sync-only limitation

**Rationale**:

**Ecosystem & Community**:
- **Tortoise ORM**: Smaller community, fewer third-party integrations
- **SQLAlchemy**: Industry standard, massive ecosystem (Alembic, pytest plugins, monitoring tools)
- **Documentation**: SQLAlchemy has comprehensive docs, books, and Stack Overflow answers
- **Stability**: SQLAlchemy is battle-tested in production for 15+ years

**Feature Set**:
- **Complex Queries**: SQLAlchemy's query builder is more powerful
  ```python
  # SQLAlchemy: Advanced joins and subqueries
  result = await db.execute(
      select(Product)
      .join(ProductSnapshot)
      .where(ProductSnapshot.price < Product.current_price * 0.9)
      .options(selectinload(Product.snapshots))
  )
  ```
- **Hybrid Properties**: Computed fields with both Python and SQL expressions
- **Raw SQL Flexibility**: Easy to drop to raw SQL when needed
- **Migration Tools**: Alembic is the gold standard for schema migrations

**Type Safety**:
- **Tortoise ORM**: Limited type hints, some runtime magic
- **SQLAlchemy 2.0**: Full type safety with `Mapped[T]` syntax
  ```python
  class Product(Base):
      id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
      title: Mapped[str] = mapped_column(String(500))
      price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
      snapshots: Mapped[list["ProductSnapshot"]] = relationship()
  ```
- **Mypy Support**: Better static type checking, fewer runtime errors

**Performance**:
- **Tortoise ORM**: Good async performance
- **SQLAlchemy 2.0**: Comparable async performance + more optimization options
- **Connection Pooling**: SQLAlchemy's pooling is more mature and configurable
- **Query Optimization**: Better control over eager loading, lazy loading, and query caching

**Implementation**:

**Migration Process** (detailed in `backend/TORTOISE_ORM_MIGRATION.md`):

1. **Phase 1 - Setup SQLAlchemy**:
   ```python
   # core/database.py
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

   engine = create_async_engine(
       DATABASE_URL,
       echo=settings.DEBUG,
       pool_pre_ping=True,
       pool_size=10,
       max_overflow=20
   )

   async_session_maker = async_sessionmaker(
       engine,
       class_=AsyncSession,
       expire_on_commit=False
   )
   ```

2. **Phase 2 - Convert Models**:
   ```python
   # Before (Tortoise ORM)
   from tortoise import fields
   from tortoise.models import Model

   class Product(Model):
       id = fields.UUIDField(pk=True)
       title = fields.CharField(max_length=500)
       price = fields.DecimalField(max_digits=10, decimal_places=2)

   # After (SQLAlchemy 2.0)
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

   class Base(DeclarativeBase):
       pass

   class Product(Base):
       __tablename__ = "products"

       id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
       title: Mapped[str] = mapped_column(String(500))
       price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
   ```

3. **Phase 3 - Repository Pattern**:
   ```python
   # Introduced repository pattern for data access
   class ProductRepository:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def get_by_id(self, product_id: UUID) -> Product | None:
           result = await self.db.execute(
               select(Product).where(Product.id == product_id)
           )
           return result.scalar_one_or_none()
   ```

4. **Phase 4 - Alembic Migrations**:
   ```bash
   # Initialize Alembic
   uv run alembic init alembic

   # Generate initial migration from existing schema
   uv run alembic revision --autogenerate -m "initial_schema"

   # Apply migration
   uv run alembic upgrade head
   ```

5. **Phase 5 - Update API Routes**:
   ```python
   # Dependency injection for database session
   async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
       async with async_session_maker() as session:
           yield session

   @router.get("/products/{product_id}")
   async def get_product(
       product_id: UUID,
       db: AsyncSession = Depends(get_async_db)
   ):
       repo = ProductRepository(db)
       product = await repo.get_by_id(product_id)
       if not product:
           raise HTTPException(status_code=404)
       return product
   ```

**Trade-offs**:

 **Pros**:
- **Ecosystem**: Access to entire SQLAlchemy ecosystem (Alembic, Flask-SQLAlchemy patterns, etc.)
- **Type Safety**: Better static type checking with mypy
- **Documentation**: Comprehensive official docs + community resources
- **Advanced Features**: Hybrid properties, query optimization, custom types
- **Industry Standard**: Easier to hire developers familiar with SQLAlchemy
- **Flexibility**: Can optimize queries at very granular level

 **Cons**:
- **Migration Effort**: ~40 hours of development time to migrate all models and queries
- **Learning Curve**: SQLAlchemy 2.0 syntax is different from Tortoise ORM
- **Verbosity**: More boilerplate code than Tortoise ORM
- **Initial Setup**: More complex configuration (engine, session maker, dependencies)

**Conclusion**: SQLAlchemy 2.0 was the right choice for a production-grade, long-term maintainable codebase with complex data requirements.


---

### ADR-006: Celery to Dramatiq Migration

**Decision**: Migrate from Celery to Dramatiq for background task processing

**Context**:
- Initially implemented background jobs with Celery (industry standard task queue)
- As project evolved, encountered complexity in configuration and maintenance
- Async/await patterns in FastAPI clashed with Celery's sync-first design
- Dramatiq emerged as lighter-weight, async-friendly alternative

**Rationale**:

**Simplicity & Developer Experience**:
- **Celery**: Complex configuration, many moving parts (broker, backend, workers, beat scheduler)
- **Dramatiq**: Minimal configuration, decorator-based API, simpler mental model
  ```python
  # Dramatiq: Simple and clean
  @dramatiq.actor(max_retries=3)
  def scrape_product(product_id: str):
      asyncio.run(async_scrape_logic(product_id))

  scrape_product.send(product_id="B01ABC123")

  # Celery: More configuration needed
  @celery_app.task(bind=True, max_retries=3)
  def scrape_product(self, product_id: str):
      # Sync code or complex async handling
  ```

**Async/Await Support**:
- **Celery**: Primarily designed for sync code, async support feels bolted-on
- **Dramatiq**: Works seamlessly with async task methods
- **Pattern**: Wrap async functions cleanly without complex workarounds

**Monitoring & Debugging**:
- **Celery**: Flower dashboard, but requires separate service
- **Dramatiq**: Simpler logging, integrates with standard Python logging
- **Our Approach**: Use Prometheus + Grafana for monitoring (works with both)

**Implementation**:

**Migration Process**:

1. **Phase 1 - Setup Dramatiq**:
   ```python
   # core/dramatiq_app.py
   import dramatiq
   from dramatiq.brokers.redis import RedisBroker
   from dramatiq.middleware import AgeLimit, TimeLimit, Retries

   redis_broker = RedisBroker(url=settings.REDIS_URL)
   redis_broker.add_middleware(AgeLimit(max_age=3600000))  # 1 hour
   redis_broker.add_middleware(TimeLimit(time_limit=900000))  # 15 min
   redis_broker.add_middleware(Retries(max_retries=3))

   dramatiq.set_broker(redis_broker)
   ```

2. **Phase 2 - Convert Tasks**:
   ```python
   # Before (Celery)
   @celery_app.task(bind=True, max_retries=3)
   def scrape_product_task(self, product_id: str):
       try:
           # Sync code or complex async handling
           result = scrape_product_sync(product_id)
           return result
       except Exception as exc:
           raise self.retry(exc=exc, countdown=60)

   # After (Dramatiq)
   @dramatiq.actor(max_retries=3, min_backoff=60000, max_backoff=300000)
   def scrape_product(product_id: str) -> None:
       async def _scrape():
           try:
               result = await scrape_product_async(product_id)
               await save_to_db(result)
           except Exception as exc:
               logger.error(f"Scrape failed: {exc}")
               raise  # Dramatiq handles retries automatically

       asyncio.run(_scrape())
   ```

3. **Phase 3 - Periodic Tasks (APScheduler)**:
   ```python
   # Replaced Celery Beat with APScheduler
   from apscheduler.schedulers.blocking import BlockingScheduler
   from tasks.scraping_tasks import scrape_all_products

   scheduler = BlockingScheduler()

   @scheduler.scheduled_job('cron', hour=2, minute=0)
   def daily_scrape():
       """Scrape all products at 2 AM daily"""
       scrape_all_products.send()

   @scheduler.scheduled_job('interval', minutes=30)
   def periodic_health_check():
       """Health check every 30 minutes"""
       check_system_health.send()

   scheduler.start()
   ```

4. **Phase 4 - Docker Compose Setup**:
   ```yaml
   # docker-compose.yml
   services:
     worker:
       build:
         context: .
         target: worker
       command: dramatiq core.dramatiq_app --processes 4 --threads 8
       environment:
         - REDIS_URL=redis://redis:6379/0
       depends_on:
         - redis

     scheduler:
       build:
         context: .
         target: scheduler
       command: python -m core.scheduler
       environment:
         - REDIS_URL=redis://redis:6379/0
       depends_on:
         - redis
   ```

5. **Phase 5 - Enqueue Tasks from API**:
   ```python
   # API endpoint triggering background task
   @router.post("/products/import")
   async def import_product(
       url: str,
       db: AsyncSession = Depends(get_async_db),
       current_user: User = Depends(get_current_user)
   ):
       # Extract ASIN from URL
       asin = extract_asin_from_url(url)

       # Enqueue background task
       scrape_product.send(product_id=asin)

       return {"status": "queued", "asin": asin}
   ```

**Trade-offs**:

 **Pros**:
- **Simplicity**: 50% less configuration code
- **Async-Friendly**: Seamless integration with FastAPI's async patterns
- **Memory Efficient**: 40% lower memory usage per worker
- **Faster Startup**: Workers start 3x faster
- **Simpler Stack**: Redis for both cache and task queue (one service)
- **Better Errors**: Clearer error messages and stack traces

 **Cons**:
- **Smaller Ecosystem**: Fewer third-party plugins (no Flower equivalent)
- **Less Enterprise Features**: No built-in result backends, task routing is simpler
- **Monitoring**: Need to build custom monitoring (we use Prometheus)
- **Community**: Smaller community than Celery (but very active)
- **Migration Cost**: ~20 hours to migrate all Celery tasks

**Conclusion**: Dramatiq was the right choice for our async-first architecture and startup constraints. The simplicity gain and cost savings outweighed the loss of enterprise features we didn't need.

---
