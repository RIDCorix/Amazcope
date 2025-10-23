# GitHub Copilot Instructions for Amazope Project

> **Purpose**: Guide AI coding agents (GitHub Copilot, Cursor, Cline, etc.) when working in this codebase.
> **Last Updated**: 2025-10-23
> **Project**: Amazcope - Amazon Monitoring & Optimization System

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Tech Stack](#architecture--tech-stack)
3. [Development Setup](#development-setup)
4. [Code Patterns & Conventions](#code-patterns--conventions)
5. [Key Workflows](#key-workflows)
6. [Testing Guidelines](#testing-guidelines)
7. [Deployment](#deployment)
8. [File Structure Reference](#file-structure-reference)
9. [Common Commands](#common-commands)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

**Amazcope** is a production-ready **Amazon Monitoring & Optimization System** with:

- **Real-time product tracking**: Monitor prices, rankings, and competitor activity
- **AI-powered optimization**: OpenAI-driven listing improvement suggestions
- **Automated scraping**: Apify integration for reliable Amazon data extraction
- **Background processing**: Dramatiq workers + APScheduler for async tasks (scraping, alerts, reports)
- **Multi-tenancy**: User-based access with JWT authentication
- **Comprehensive monitoring**: Prometheus + Grafana dashboards

### Business Logic Flow

```
User → JWT Auth → Product Management → Scraping Jobs (Dramatiq + Apify)
  ↓
Snapshots (Time-series data) → Change Detection → Alerts → Email/Webhook
  ↓
Analytics & Reports → AI Optimization (OpenAI) → Listing Suggestions
  ↓
Scheduled Tasks (APScheduler) → Daily Updates, Cleanups, AI Suggestions
```

---

## 🏗️ Architecture & Tech Stack

### Backend (`backend/`)

- **Framework**: FastAPI 0.115+ (async Python web framework)
- **ORM**: SQLAlchemy 2.0+ (async) with Alembic migrations
- **Database**: PostgreSQL (via Supabase or AWS RDS)
- **Queue/Cache**: Redis 7.0+
- **Task Queue**: Dramatiq 1.18+ (with Redis broker)
- **Task Scheduler**: APScheduler 3.10+ (cron-style periodic tasks)
- **Package Manager**: `uv` (Astral's ultra-fast Python package installer)
- **Monitoring**: Prometheus FastAPI Instrumentator + Grafana
- **Error Tracking**: Sentry

### Frontend (`frontend/`)

- **Framework**: Vite + React 18+ (TypeScript)
- **Routing**: React Router DOM v6
- **UI Library**: Radix UI + Tailwind CSS + shadcn/ui
- **Rich Text**: Editor.js with custom plugins
- **Charts**: Recharts
- **Internationalization**: Custom i18n with hooks
- **State Management**: React Hook Form + Context API
- **Build Tool**: Vite 5+ (ultra-fast HMR)

### Infrastructure (`deployment/terraform/`)

- **IaC**: Terraform (AWS: VPC, RDS, ElastiCache, ECS Fargate, ALB)
- **Container Registry**: DockerHub
- **Deployment Options**:
  - **Zeabur** (recommended): Managed platform with auto-scaling
  - **Custom Server**: SSH-based Docker Compose deployment

### CI/CD (`.github/workflows/cd.yml`)

- **Multi-stage Docker builds**: 3 targets (`base`, `dependencies`, `api`, `worker`, `scheduler`)
- **GitHub Actions**: Build → Push to DockerHub → Deploy
- **Terraform Auto-Backfill**: Infrastructure outputs → GitHub Secrets (automated)
- **Health Checks**: Automated validation before traffic routing

---

## 🚀 Development Setup

### Prerequisites

- **Python**: 3.11+ (required for backend)
- **Node.js**: 18.0+ (required for frontend)
- **Docker & Docker Compose**: 24.0+ (required for local development)
- **uv**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Quick Start

#### 1. Clone and Setup Environment

```bash
# Clone repository
git clone <repo-url> amazcope
cd amazcope

# Backend setup
cd backend
cp .env.example .env  # Edit with your credentials
uv sync  # Install dependencies

# Frontend setup
cd ../frontend
npm install
cp .env.local.example .env.local  # Edit with API URL
```

#### 2. Database Migrations

```bash
cd backend/src
uv run alembic upgrade head  # Apply existing migrations
# OR
uv run alembic init alembic  # Initialize Alembic (first time)
```

#### 3. Start Development Services

**Option A: Full Stack with Docker Compose**
```bash
cd backend
docker-compose up -d  # Starts API, worker, APScheduler, Redis, PostgreSQL, Prometheus, Grafana
```

**Option B: Individual Services (for development)**
```bash
# Terminal 1: API Server
cd backend/src
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Dramatiq Worker
cd backend/src
uv run dramatiq core.dramatiq_app --processes 4 --threads 8

# Terminal 3: APScheduler (periodic tasks)
cd backend/src
uv run python -m core.scheduler

# Terminal 4: Frontend
cd frontend
npm run dev  # Vite dev server on port 5173
```

#### 4. Verify Setup

- **API**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:5173 (Vite dev server)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

---

## 📐 Code Patterns & Conventions

### 1. Backend Patterns

#### Repository Pattern (Data Access Layer)

**Location**: `backend/src/repositories/`

```python
from sqlalchemy.orm import Session
from products.models import Product
from schemas.product import ProductCreate, ProductUpdate

class ProductRepository:
    """Encapsulates all data access logic for Product model."""

    def __init__(self, db: Session):
        self.db = db

    def get_product(self, product_id: int) -> Product:
        """Retrieve single product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_products(self, skip: int = 0, limit: int = 10) -> list[Product]:
        """Retrieve paginated products."""
        return self.db.query(Product).offset(skip).limit(limit).all()

    def create_product(self, product: ProductCreate) -> Product:
        """Create new product."""
        db_product = Product(**product.dict())
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product
```

**When to use**:
- All database CRUD operations
- Complex queries with joins/filters
- Business logic that touches data

#### Async/Await Everywhere

**Backend is async-first** - always use `async def` and `await`:

```python
# ✅ CORRECT
from sqlalchemy import select

async def get_user(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# ❌ WRONG - Don't mix sync code in async context
def get_user(user_id: int) -> User:
    return db.query(User).get(user_id)  # Blocks event loop!
```

#### Pydantic Schemas for Validation

**Location**: `backend/src/schemas/`

```python
from pydantic import BaseModel, Field, field_validator

class ProductCreate(BaseModel):
    """Schema for creating a product."""
    asin: str = Field(..., min_length=10, max_length=10)
    title: str = Field(..., min_length=1, max_length=500)
    price: float = Field(..., gt=0)

    @field_validator('asin')
    @classmethod
    def validate_asin(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('ASIN must be alphanumeric')
        return v.upper()

class ProductResponse(BaseModel):
    """Schema for product responses."""
    id: int
    asin: str
    title: str
    price: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode
```

**Always use**:
- `ProductCreate` for POST requests
- `ProductUpdate` for PUT/PATCH
- `ProductResponse` for GET responses

#### Dependency Injection (FastAPI)

```python
from fastapi import Depends
from api.deps import get_current_user, get_db

@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Dependencies are automatically resolved by FastAPI."""
    return await ProductRepository(db).get_product(product_id)
```

#### Dramatiq Actor Patterns

**Location**: `backend/src/tasks/`

```python
import dramatiq
import asyncio
from core.dramatiq_app import dramatiq
from utils.amazon_scraper import scrape_product_data

@dramatiq.actor(max_retries=3, min_backoff=60000, max_backoff=300000)
def scrape_product(product_id: str) -> None:
    """Scrape product data from Amazon via Apify.

    Args:
        product_id: Amazon ASIN
    """
    async def _scrape() -> None:
        try:
            product_data = await scrape_product_data(product_id)
            if product_data:
                await ProductRepository.save_product_data(product_data)
                logger.info(f"Product {product_id} scraped successfully")
        except Exception as exc:
            logger.error(f"Failed to scrape product {product_id}: {str(exc)}")
            raise  # Dramatiq will handle retries via middleware

    asyncio.run(_scrape())

# Schedule periodic tasks with APScheduler
# In core/scheduler.py:
from apscheduler.schedulers.blocking import BlockingScheduler
from products.tasks import scrape_all_products

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=2, minute=0)
def daily_product_scrape():
    """Scrape all products daily at 2 AM."""
    scrape_all_products.send()
```

**Actor Best Practices**:
- ✅ Use `@dramatiq.actor` decorator for background tasks
- ✅ Add `max_retries`, `min_backoff`, `max_backoff` for resilience (in milliseconds)
- ✅ Wrap async code with `asyncio.run()` since Dramatiq runs in sync context
- ✅ Use `.send()` to enqueue tasks (not `.delay()`)
- ✅ Log everything with `loguru`
- ✅ Let Dramatiq middleware handle retries automatically

### 2. Frontend Patterns

#### **CRITICAL: Always Use Service Layer - Never Use Fetch Directly**

**❌ WRONG - Don't use fetch directly**:
```typescript
// BAD: Direct fetch calls bypass error handling and auth interceptors
const response = await fetch('http://localhost:8000/api/v1/products', {
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
const data = await response.json();
```

**✅ CORRECT - Use apiClient via service layer**:
```typescript
// GOOD: Use the service layer
import { productService } from '@/services/productService';

const product = await productService.getProduct(123);
```

**Why?**
- ✅ Automatic JWT token injection
- ✅ Centralized error handling
- ✅ Automatic token refresh on 401
- ✅ Type safety with TypeScript
- ✅ Consistent base URL
- ✅ Request/response interceptors
- ✅ Snake_case ↔ camelCase conversion

#### API Client Setup

**Location**: `frontend/src/lib/api.ts`

```typescript
import axios from 'axios';

// Configured apiClient with interceptors
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatic JWT token injection
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Automatic token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token refresh logic here
    }
    return Promise.reject(error);
  }
);
```

#### Service Layer Pattern

**Always create services in** `frontend/src/services/`

```typescript
// frontend/src/services/productService.ts
import apiClient from '@/lib/api';

export interface Product {
  id: number;
  asin: string;
  title: string;
  price: number;
  created_at: string;
}

export const productService = {
  // GET /api/v1/tracking/products/{id}
  async getProduct(id: number): Promise<Product> {
    const response = await apiClient.get(`/api/v1/tracking/products/${id}`);
    return response.data;
  },

  // POST /api/v1/tracking/products
  async createProduct(product: Partial<Product>): Promise<Product> {
    const response = await apiClient.post('/api/v1/tracking/products', product);
    return response.data;
  },

  // DELETE /api/v1/tracking/products/{id}
  async deleteProduct(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/tracking/products/${id}`);
  },
};
```

**Usage in Components**:
```typescript
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { productService, type Product } from '@/services/productService';

export default function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const data = await productService.getProduct(Number(id));
      setProduct(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load product');
    } finally {
      setLoading(false);
    }
  };

  // Component JSX...
}
```

#### Existing Services

**Available services** (use these, don't recreate):
- `authService` - Login, register, logout, profile
- `productService` - Product CRUD, import from URL, reviews, bestsellers
- `imageService` - Image upload and retrieval

**Example**: Import from URL
```typescript
import { productService } from '@/services/productService';

const handleImport = async () => {
  try {
    const product = await productService.importFromUrl({
      url: 'https://www.amazon.com/dp/B07XJ8C8F5',
      price_change_threshold: 10.0,
      bsr_change_threshold: 30.0,
      scrape_reviews: true,
      scrape_bestsellers: true,
    });
    console.log('Imported:', product);
  } catch (error) {
    console.error('Import failed:', error);
  }
};
```

### 3. Configuration Management

#### Environment Variables

**Backend** (`backend/.env`):
```bash
# Database (Supabase or PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=amazcope
DATABASE_URL=postgresql://postgres:password@localhost:5432/amazcope

# Redis
REDIS_URL=redis://localhost:6379/0

# Dragatiq
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# External Services
APIFY_API_TOKEN=your-apify-token
OPENAI_API_KEY=sk-...

# Monitoring (optional)
SENTRY_DSN=https://...@sentry.io/...
```

**Frontend** (`frontend/.env.local`):
```bash
VITE_API_URL=http://localhost:8000
NODE_ENV=development
```

#### Pydantic Settings (Backend)

**Location**: `backend/src/core/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Amazcope"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Redis
    REDIS_URL: str | None = None

    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars
    )

# Singleton instance
settings = Settings()
```

**Usage**:
```python
from core.config import settings

database_url = settings.DATABASE_URL
```

---

## 🔄 Key Workflows

### Adding a New API Endpoint

1. **Define Pydantic Schema** (`backend/src/schemas/`)
   ```python
   class AlertCreate(BaseModel):
       product_id: int
       threshold: float
   ```

2. **Create Repository Method** (`backend/src/repositories/`)
   ```python
   class AlertRepository:
       async def create_alert(self, alert: AlertCreate) -> Alert:
           # Data access logic
   ```

3. **Add API Route** (`backend/src/api/v1/alerts.py`)
   ```python
   @router.post("/", response_model=AlertResponse)
   async def create_alert(
       alert: AlertCreate,
       db: Session = Depends(get_async_db),
       user: User = Depends(get_current_user)
   ):
       repo = AlertRepository(db)
       return await repo.create_alert(alert)
   ```

4. **Register Router** (`backend/src/api/v1/router.py`)
   ```python
   from api.v1 import alerts
   api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
   ```

5. **Write Tests** (`backend/tests/test_api/test_alerts.py`)
   ```python
   async def test_create_alert(client, auth_headers):
       response = await client.post("/api/v1/alerts", json={...}, headers=auth_headers)
       assert response.status_code == 201
   ```

### Creating a Database Migration

```bash
cd backend/src

# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "add_alerts_table"

# Review generated migration in alembic/versions/

# Apply migration
uv run alembic upgrade head

# Rollback if needed
uv run alembic downgrade -1
```

**Important**: Always review auto-generated migrations before applying!

### Adding a Dramatiq Task

1. **Define Task** (`backend/src/tasks/alert_tasks.py`)
   ```python
   import dramatiq
   import asyncio
   from core.dramatiq_app import dramatiq

   @dramatiq.actor(max_retries=3, min_backoff=60000, max_backoff=300000)
   def send_price_alert(product_id: int, new_price: float) -> None:
       """Send price alert for product."""
       async def _send() -> None:
           # Task logic
           pass

       asyncio.run(_send())
   ```

2. **Schedule Task** (if periodic)
   ```python
   # In core/scheduler.py
   from apscheduler.schedulers.blocking import BlockingScheduler
   from tasks.alert_tasks import send_daily_price_alerts

   scheduler = BlockingScheduler()

   @scheduler.scheduled_job('cron', hour=0, minute=0)
   def daily_price_check():
       """Check prices daily at midnight."""
       send_daily_price_alerts.send()
   ```

3. **Call Task from API**
   ```python
   from tasks.alert_tasks import send_price_alert

   # Execute async (enqueue task)
   send_price_alert.send(product_id=123, new_price=29.99)

   # Execute with delay (schedule for later)
   send_price_alert.send_with_options(
       args=(123, 29.99),
       delay=3600000  # 1 hour in milliseconds
   )
   ```

4. **Monitor Tasks**
   - View Dramatiq worker logs: `docker-compose logs -f worker`
   - Check Prometheus metrics: http://localhost:9090
   - View task execution in worker console output

### Updating Frontend with Backend Changes

1. **Generate TypeScript Types** (if backend OpenAPI schema updated)
   ```bash
   cd frontend
   npm run generate-api  # Runs scripts/generate-api-schema.sh
   ```

2. **Update Service Layer** (`frontend/src/services/`)
   ```typescript
   export const alertService = {
     async createAlert(alert: AlertCreate): Promise<Alert> {
       const { data } = await apiClient.post('/api/v1/alerts', alert);
       return data;
     }
   };
   ```

3. **Use in Components**
   ```tsx
   import { alertService } from '@/services/alert-service';

   const handleCreateAlert = async () => {
     try {
       const alert = await alertService.createAlert({ product_id: 1, threshold: 25.0 });
       toast.success('Alert created!');
     } catch (error) {
       toast.error('Failed to create alert');
     }
   };
   ```

---

## 🧪 Testing Guidelines

### Backend Testing

**Location**: `backend/tests/`

**Structure**:
```
tests/
├── conftest.py              # Shared fixtures (DB session, test client)
├── test_api/                # API endpoint tests
│   ├── test_auth.py
│   ├── test_products.py
│   └── test_alerts.py
├── test_services/           # Service layer tests
│   ├── test_product_service.py
│   └── test_scraper_service.py
└── test_utils/              # Utility function tests
    └── test_amazon_scraper.py
```

**Fixtures** (`conftest.py`):
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base

@pytest.fixture(scope='session')
def engine():
    """Test database engine."""
    return create_engine('postgresql://test:test@localhost:5433/test_db')

@pytest.fixture(scope='session')
def tables(engine):
    """Create all tables for testing."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope='function')
def db_session(engine, tables):
    """Provide a transactional database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def auth_headers(test_user):
    """Provide JWT auth headers."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

**Example Test**:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, auth_headers: dict):
    """Test product creation endpoint."""
    payload = {
        "asin": "B01ABCD123",
        "title": "Test Product",
        "price": 29.99
    }

    response = await client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["asin"] == payload["asin"]
    assert data["id"] is not None
```

**Run Tests**:
```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_api/test_products.py

# Run tests matching pattern
uv run pytest -k "test_create"

# Run with verbose output
uv run pytest -v
```

### Frontend Testing

**Framework**: Jest + React Testing Library

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:ci

# Watch mode
npm run test:watch
```

**Example Test**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from '@/components/ProductCard';

describe('ProductCard', () => {
  it('renders product information', () => {
    const product = {
      id: 1,
      asin: 'B01ABCD123',
      title: 'Test Product',
      price: 29.99
    };

    render(<ProductCard product={product} />);

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('$29.99')).toBeInTheDocument();
  });

  it('calls onAddToCart when button clicked', () => {
    const mockOnAdd = jest.fn();
    render(<ProductCard product={product} onAddToCart={mockOnAdd} />);

    fireEvent.click(screen.getByRole('button', { name: /add to cart/i }));
    expect(mockOnAdd).toHaveBeenCalledTimes(1);
  });
});
```

---

## 🚢 Deployment

### Option 1: Zeabur (Recommended)

**Prerequisites**: Only need DockerHub credentials

1. **Setup GitHub Secrets**
   ```bash
   cd scripts
   # Create .github.secrets file (see setup/github/.github.secrets.example)
   ./setup-github-secrets.sh
   ```

2. **Push to GitHub**
   ```bash
   git push origin main
   ```

3. **GitHub Actions Workflow**
   - Builds 3 Docker images: `api`, `worker`, `scheduler`
   - Pushes to DockerHub with tags: `latest`, `<commit-sha>`
   - Zeabur auto-deploys from DockerHub

4. **Zeabur Configuration** (`backend/zeabur.json`)
   - Pre-configured with 5 services: api, worker, scheduler, redis, frontend
   - Auto-scaling enabled for api (1-10 replicas) and worker (1-5 replicas)
   - Health checks on `/health` endpoint
   - Internal networking between services

**Required GitHub Secrets (Zeabur)**:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

**Optional** (set AFTER first deployment):
- `DEPLOY_HOST` (Zeabur assigns dynamically)

### Option 2: Custom Server (SSH Deployment)

**Prerequisites**: Server with Docker + SSH access

1. **Setup GitHub Secrets**
   ```bash
   # Add to .github.secrets:
   DEPLOY_HOST=your-server.com
   DEPLOY_USER=deploy
   DEPLOY_SSH_KEY=<paste multi-line SSH private key>

   ./scripts/setup-github-secrets.sh
   ```

2. **Deploy via GitHub Actions**
   - Workflow connects to server via SSH
   - Pulls latest images from DockerHub
   - Runs `docker-compose -f docker-compose.prod.yml up -d`
   - Health check validation

3. **Manual Deployment**
   ```bash
   # SSH to server
   ssh deploy@your-server.com

   cd /path/to/amazcope
   git pull origin main

   # Pull latest images
   docker-compose -f docker-compose.prod.yml pull

   # Restart services
   docker-compose -f docker-compose.prod.yml up -d

   # Check health
   curl http://localhost:8000/health
   ```

### Option 3: Terraform (AWS Infrastructure)

**Prerequisites**: AWS account + Terraform installed

1. **Configure Terraform Variables**
   ```bash
   cd deployment/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your AWS credentials and settings
   ```

2. **Initialize Terraform**
   ```bash
   terraform init
   ```

3. **Apply Infrastructure**
   ```bash
   terraform plan  # Preview changes
   terraform apply  # Create resources
   ```

4. **Auto-Backfill to GitHub Secrets**
   - CD workflow automatically extracts Terraform outputs:
     - `deploy_host` → `DEPLOY_HOST`
     - `app_url` → `APP_URL`
     - `sentry_org` → `SENTRY_ORG`
     - `sentry_project` → `SENTRY_PROJECT`
     - `sentry_auth_token` → `SENTRY_AUTH_TOKEN`
   - Uses GitHub CLI to update repository secrets
   - No manual copy-paste needed!

**Resources Created**:
- VPC with public/private subnets
- RDS PostgreSQL (multi-AZ optional)
- ElastiCache Redis
- ECS Fargate cluster (3 services: api, worker, scheduler)
- Application Load Balancer
- CloudWatch logs and alarms
- Secrets Manager for sensitive data

### Docker Multi-Stage Build

**Dockerfile** (`backend/Dockerfile`):
- **5 build targets**: `base`, `dependencies`, `api`, `worker`, `scheduler`
- **Security**: Non-root user, bytecode compilation, minimal image size
- **Performance**: `uv` package manager (10x faster than pip)

```dockerfile
# Build API image
docker build --target api -t amazcope-api:latest .

# Build worker image
docker build --target worker -t amazcope-worker:latest .

# Build scheduler image
docker build --target scheduler -t amazcope-scheduler:latest .

# Build with build args
docker build --build-arg PYTHON_VERSION=3.11 --target api -t amazcope-api:latest .
```

### Environment-Specific Configurations

**Development** (`docker-compose.yml`):
- Local builds with volume mounts (hot reload)
- Exposed ports for debugging
- Single replica for each service

**Production** (`docker-compose.prod.yml`):
- Uses DockerHub images only (no local builds)
- 2 API replicas, 2 worker replicas, 1 scheduler replica
- Resource limits (CPU: 0.5-2, Memory: 512MB-2GB)
- Health checks with restart policies
- 90-day Prometheus data retention

---

## 📂 File Structure Reference

### Key Files & Directories

```
amazcope/
├── backend/
│   ├── src/
│   │   ├── main.py                    # FastAPI entrypoint (START HERE)
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic settings (environment variables)
│   │   │   ├── database.py            # SQLAlchemy async setup
│   │   │   ├── dramatiq_app.py        # Dramatiq broker configuration
│   │   │   └── scheduler.py           # APScheduler configuration
│   │   ├── api/
│   │   │   ├── deps.py                # Dependency injection (get_db, get_current_user)
│   │   │   └── v1/                    # API routes
│   │   │       ├── router.py          # Main API router
│   │   │       ├── auth.py            # JWT authentication endpoints
│   │   │       ├── products.py        # Product CRUD
│   │   │       ├── alerts.py          # Alert management
│   │   │       └── reports.py         # Report generation
│   │   ├── models/                    # SQLAlchemy models (database tables)
│   │   │   ├── base.py                # Base model with common fields
│   │   │   ├── user.py                # User model
│   │   │   ├── product.py             # Product model
│   │   │   ├── snapshot.py            # ProductSnapshot (time-series data)
│   │   │   ├── competitor.py          # Competitor relations
│   │   │   ├── alert.py               # Alert model
│   │   │   └── report.py              # Report model
│   │   ├── repositories/              # Data access layer (repository pattern)
│   │   │   ├── user_repository.py
│   │   │   ├── product_repository.py
│   │   │   ├── alert_repository.py
│   │   │   └── price_history_repository.py
│   │   ├── schemas/                   # Pydantic models (request/response validation)
│   │   │   ├── user.py                # UserCreate, UserOut, UserUpdate
│   │   │   ├── product.py             # ProductCreate, ProductResponse, ProductUpdate
│   │   │   ├── alert.py
│   │   │   └── report.py
│   │   ├── services/                  # External integrations & business logic
│   │   │   ├── apify_client.py        # Amazon scraping via Apify
│   │   │   ├── openai_client.py       # AI optimization suggestions
│   │   │   └── cache_service.py       # Redis caching utilities
│   │   ├── tasks/                     # Dramatiq actors (background tasks)
│   │   │   ├── scraping_tasks.py      # Product scraping jobs
│   │   │   ├── alert_tasks.py         # Alert notifications
│   │   │   ├── analytics_tasks.py     # Data analytics & reports
│   │   │   └── price_monitoring_tasks.py
│   │   ├── middleware/                # Custom middleware
│   │   │   ├── rate_limit.py          # Rate limiting
│   │   │   └── logging.py             # Request logging
│   │   └── utils/                     # Common utilities
│   │       ├── logger.py              # Loguru configuration
│   │       ├── security.py            # JWT, password hashing
│   │       └── helpers.py             # Common functions
│   ├── tests/                         # Pytest test suite
│   │   ├── conftest.py                # Shared fixtures
│   │   ├── test_api/                  # API endpoint tests
│   │   ├── test_services/             # Service layer tests
│   │   └── test_utils/                # Utility tests
│   ├── alembic/                       # Alembic database migrations
│   │   └── versions/                  # Migration scripts
│   ├── prometheus/                    # Prometheus configuration
│   │   └── prometheus.yml             # Scrape configs for all services
│   ├── grafana/                       # Grafana dashboards
│   ├── Dockerfile                     # Multi-stage Docker build
│   ├── docker-compose.yml             # Development setup
│   ├── docker-compose.prod.yml        # Production setup
│   ├── pyproject.toml                 # Python dependencies + tool configs
│   ├── zeabur.json                    # Zeabur deployment config
│   └── .env.example                   # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── app/                       # React app pages/routes
│   │   ├── components/                # React components
│   │   ├── lib/
│   │   │   └── api.ts                 # Axios instance with interceptors
│   │   ├── services/                  # API service layer
│   │   │   ├── authService.ts
│   │   │   ├── productService.ts
│   │   │   └── alertService.ts
│   │   ├── types/
│   │   │   └── api.ts                 # TypeScript types (auto-generated)
│   │   ├── hooks/                     # Custom React hooks
│   │   └── i18n/                      # Internationalization
│   ├── public/                        # Static assets
│   │   └── i18n/locales/              # Translation files
│   ├── Dockerfile                     # Vite production build
│   ├── package.json                   # Node.js dependencies
│   ├── vite.config.ts                 # Vite configuration
│   ├── tsconfig.json                  # TypeScript configuration
│   └── .env.local.example             # Frontend environment variables
├── deployment/
│   └── terraform/                     # AWS infrastructure as code
│       ├── main.tf                    # Main Terraform configuration
│       ├── outputs.tf                 # Exported values (auto-backfilled to GitHub Secrets)
│       ├── variables.tf               # Input variables
│       ├── vpc.tf                     # VPC and networking
│       ├── rds.tf                     # PostgreSQL database
│       ├── redis.tf                   # ElastiCache Redis
│       ├── ecs.tf                     # ECS Fargate cluster
│       ├── alb.tf                     # Application Load Balancer
│       ├── monitoring.tf              # CloudWatch alarms
│       └── modules/                   # Reusable Terraform modules
├── scripts/
│   ├── setup-github-secrets.sh        # Automate GitHub secret deployment
│   └── setup-env-file.sh              # Generate .env with secure defaults
├── setup/
│   └── github/
│       ├── .github.secrets.example    # Template for GitHub secrets
│       └── .github.env.example        # Template for environment variables
├── .github/
│   ├── workflows/
│   │   └── cd.yml                     # Continuous deployment workflow
│   └── copilot-instructions.md        # THIS FILE - AI coding guidelines
├── .gitignore                         # Ignore .env, secrets, SSH keys
└── README.md                          # Project documentation
```

---

## ⚡ Common Commands

### Backend Development

```bash
# Install dependencies
uv sync

# Run API server (with hot reload)
cd backend/src
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run Dramatiq worker
uv run dramatiq core.dramatiq_app --processes 4 --threads 8

# Run APScheduler (periodic tasks)
uv run python -m core.scheduler

# Database migrations
uv run alembic upgrade head                       # Apply migrations
uv run alembic revision --autogenerate -m "add_feature"  # Create migration
uv run alembic downgrade -1                       # Rollback last migration
uv run alembic history                            # View migration history

# Testing
uv run pytest                          # Run all tests
uv run pytest --cov=src                # With coverage
uv run pytest -v                       # Verbose output
uv run pytest -k "test_create"         # Run specific tests

# Code quality
uv run ruff check src/                 # Lint code
uv run ruff check src/ --fix           # Auto-fix issues
uv run mypy src/                       # Type checking

# Docker
docker-compose up -d                   # Start all services
docker-compose down                    # Stop all services
docker-compose logs -f api             # View API logs
docker-compose exec api bash           # Shell into API container
```

### Frontend Development

```bash
# Install dependencies
npm install

# Development server (hot reload)
npm run dev

# Production build
npm run build
npm start

# Testing
npm test                               # Run tests
npm run test:ci                        # CI mode (coverage)
npm run test:watch                     # Watch mode

# Code quality
npm run lint                           # ESLint
npm run lint:fix                       # Auto-fix issues
npm run format                         # Prettier
npm run type-check                     # TypeScript check

# API schema generation
npm run generate-api                   # Generate types from backend OpenAPI
```

### Deployment

```bash
# Setup GitHub secrets
cd scripts
./setup-github-secrets.sh

# Setup local .env
./setup-env-file.sh

# Docker builds (manual)
docker build --target api -t amazcope-api:latest backend/
docker build --target worker -t amazcope-worker:latest backend/
docker push amazcope-api:latest
docker push amazcope-worker:latest

# Terraform (AWS infrastructure)
cd deployment/terraform
terraform init
terraform plan
terraform apply
terraform destroy                      # CAUTION: Deletes all resources

# SSH to production server
ssh deploy@your-server.com
cd /path/to/amazcope
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError" when running backend

**Cause**: Dependencies not installed or wrong Python environment

**Fix**:
```bash
cd backend
uv sync  # Reinstall dependencies
uv run python --version  # Verify Python 3.11+
```

#### 2. Dramatiq tasks not executing

**Cause**: Worker not running or Redis connection failed

**Fix**:
```bash
# Check Redis connection
redis-cli ping  # Should return "PONG"

# Check Dramatiq worker status (view logs)
docker-compose logs -f worker

# Check APScheduler (periodic tasks)
docker-compose logs -f scheduler

# Verify tasks are being enqueued
redis-cli keys "dramatiq:*"
```

#### 3. Database migration errors

**Cause**: Migration conflicts or outdated migration history

**Fix**:
```bash
# View current migration status
uv run alembic history

# Rollback to previous state
uv run alembic downgrade -1

# Re-run migrations
uv run alembic upgrade head

# Nuclear option: Reset database (CAUTION: Deletes all data)
docker-compose down -v
docker-compose up -d postgres
uv run alembic upgrade head
```

#### 4. Frontend API calls failing (CORS errors)

**Cause**: Backend CORS origins not configured correctly

**Fix**:
```bash
# In backend/.env, ensure CORS_ORIGINS includes frontend URL
CORS_ORIGINS=http://localhost:3000,https://your-frontend.com

# Restart API server
docker-compose restart api
```

#### 5. Docker build fails with "uv not found"

**Cause**: Docker build cache issue

**Fix**:
```bash
# Clear Docker build cache
docker builder prune -a

# Rebuild without cache
docker build --no-cache --target api -t amazcope-api:latest backend/
```

#### 6. Terraform apply fails with "AuthFailure"

**Cause**: Invalid AWS credentials

**Fix**:
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Configure AWS CLI
aws configure

# Check terraform.tfvars
cd deployment/terraform
cat terraform.tfvars  # Ensure credentials are correct
```

### Performance Optimization

#### Backend

- **Use Redis caching** for expensive queries:
  ```python
  from services.cache_service import cache

  @cache.memoize(timeout=3600)  # Cache for 1 hour
  async def get_product_analytics(product_id: int):
      # Expensive computation
      return results
  ```

- **Optimize database queries** with selectinload/joinedload:
  ```python
  from sqlalchemy.orm import selectinload
  result = await db.execute(
      select(Product).options(selectinload(Product.snapshots))
  )
  products = result.scalars().all()
  ```

- **Add database indexes** for frequently queried fields:
  ```python
  from sqlalchemy import Column, String, DateTime, Index

  class Product(Base):
      asin = Column(String(10), index=True)  # Index for fast lookups
      created_at = Column(DateTime, index=True)
  ```

- **Use Dramatiq for long-running tasks**:
  ```python
  # DON'T: Block API request
  result = expensive_scraping_operation()

  # DO: Queue task
  expensive_scraping_operation.send(product_id=123)
  return {"status": "queued"}
  ```

#### Frontend

- **Implement lazy loading with React.lazy**:
  ```typescript
  const Dashboard = React.lazy(() => import('@/components/Dashboard'));

  <Suspense fallback={<Spinner />}>
    <Dashboard />
  </Suspense>
  ```

- **Use React Query for data fetching**:
  ```typescript
  const { data, isLoading } = useQuery('products', () => productService.getProducts());
  ```

- **Optimize bundle size with Vite**:
  - Use dynamic imports for large dependencies
  - Configure `build.rollupOptions` in vite.config.ts
  - Use `vite-plugin-compression` for gzip/brotli

---

## 📚 Additional Resources

### Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/en/20/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Dramatiq**: https://dramatiq.io/
- **APScheduler**: https://apscheduler.readthedocs.io/
- **Vite**: https://vitejs.dev/
- **React Router**: https://reactrouter.com/
- **Terraform AWS**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

### Monitoring Dashboards

- **Prometheus**: http://localhost:9090 - Metrics collection
- **Grafana**: http://localhost:3001 - Visualization dashboards
- **FastAPI Docs**: http://localhost:8000/docs - Interactive API documentation

---

## 🎯 Project-Specific Conventions

### Code Style

- **Backend**:
  - Use `async def` for all API routes and database operations
  - Type hints required for all functions (`mypy` enforced)
  - 100 character line length (configured in `ruff`)
  - Docstrings for all public functions (Google style)
  - Import order: stdlib → third-party → local (automatic with `ruff`)

- **Frontend**:
  - Use `const` by default, `let` only when reassignment needed
  - Prefer functional components with hooks
  - Use TypeScript `interface` for data shapes, `type` for unions/intersections
  - Extract reusable logic into custom hooks
  - Components in PascalCase, files in kebab-case

### Security Best Practices

- **Never commit secrets**: Use `.env` files (excluded in `.gitignore`)
- **Use environment variables**: Access via `settings` object (backend) or `process.env` (frontend)
- **JWT tokens**: Short expiry (30 min access, 7 day refresh)
- **Rate limiting**: Configured in `middleware/rate_limit.py`
- **Input validation**: Always use Pydantic schemas for API requests
- **SQL injection protection**: ORM handles parameterization automatically
- **CORS**: Explicitly whitelist allowed origins

### Git Workflow

- **Branch naming**: `feature/add-alerts`, `fix/scraping-timeout`, `chore/update-deps`
- **Commit messages**: Use conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Pre-commit hooks**: `ruff`, `mypy`, `prettier` run automatically
- **Pull requests**: Require tests + code review before merge

---

## 🤖 AI-Specific Guidance

### When Generating Code

1. **Always check existing patterns first**:
   - Read similar files (e.g., existing repositories before creating new ones)
   - Match naming conventions and structure

2. **Prefer async over sync**:
   - Backend is async-first, use `async def` and `await`

3. **Use type hints everywhere**:
   - Backend: Python type hints (`str`, `int`, `list[Product]`, `dict[str, Any]`)
   - Frontend: TypeScript interfaces

4. **Follow repository pattern**:
   - Don't put database logic in API routes
   - Use repository classes for data access

5. **Add tests for new features**:
   - API tests in `tests/test_api/`
   - Include positive and negative test cases

6. **Update configurations when adding dependencies**:
   - Backend: Add to `pyproject.toml` dependencies
   - Frontend: Add to `package.json`

### When Debugging

1. **Check logs first**:
   ```bash
   # Backend logs
   docker-compose logs -f api
   docker-compose logs -f worker
   docker-compose logs -f scheduler

   # Frontend logs (Vite dev server)
   npm run dev  # Console output
   ```

2. **Monitor Dramatiq tasks**:
   - View worker logs: `docker-compose logs -f worker`
   - Check Prometheus metrics: http://localhost:9090
   - Query Redis for task queue: `redis-cli keys "dramatiq:*"`

3. **Check database state**:
   ```bash
   docker-compose exec postgres psql -U postgres -d amazcope
   # Then run SQL queries
   SELECT * FROM products LIMIT 10;
   ```

4. **Use FastAPI interactive docs**:
   - Open http://localhost:8000/docs
   - Test endpoints directly in browser

### When Refactoring

1. **Run tests before and after**:
   ```bash
   uv run pytest  # Ensure no regressions
   ```

2. **Check for usages before deleting**:
   - Search codebase for function/class name
   - Consider deprecation warnings before removal

3. **Update related documentation**:
   - API docs (docstrings)
   - README updates
   - Frontend API types (`npm run generate-api`)

---

**Last Updated**: 2025-10-23
**Maintainer**: Amazcope Team
**Questions?**: Check `scripts/` for setup automation or `.github/workflows/cd.yml` for CI/CD details.
