# Amazcope - Amazon Product Monitoring & Optimization System

> **Production-ready Amazon seller tool** with AI-powered insights, real-time tracking, and automated optimization recommendations.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?style=flat&logo=React&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=flat&logo=TypeScript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=Python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg?style=flat&logo=PostgreSQL&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D.svg?style=flat&logo=Redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-24.0+-2496ED.svg?style=flat&logo=Docker&logoColor=white)](https://www.docker.com)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Development](#development)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Functionality

- **Real-Time Product Tracking**: Monitor prices, BSR rankings, reviews, and stock status
- **Smart Alerts**: Customizable thresholds for price changes and ranking fluctuations
- **AI-Powered Insights**: OpenAI-driven listing optimization suggestions
- **Analytics Dashboard**: Historical trends, competitor analysis, and performance metrics
- **Automated Scraping**: Reliable data extraction via Apify integration
- **Multi-User Support**: User-based product ownership with role-based access
- **Multi-Marketplace**: Support for Amazon US, UK, DE, JP, and more

### Advanced Features

- **Background Processing**: Async task queue with Dramatiq for non-blocking operations
- **Scheduled Jobs**: APScheduler for periodic updates and maintenance tasks
- **Batch Operations**: Bulk product imports, updates, and refreshes
- **Review Analysis**: Track and analyze customer reviews over time
- **Bestseller Tracking**: Monitor product category rankings and trends
- **Content Optimization**: AI-generated suggestions for titles, descriptions, and keywords
- **Notification System**: Email and webhook integrations for alerts
- **Monitoring & Observability**: Prometheus metrics + Grafana dashboards

---

## Architecture

### System Overview

```
┌─────────────────┐
│  Frontend (React)│
│  Port: 5173      │
└────────┬─────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│         Port: 8000                      │
├─────────────────────────────────────────┤
│  API Routes │ Authentication │ Business │
│             │  (JWT)         │  Logic   │
└──────┬──────┴────────┬───────┴──────┬───┘
       │               │              │
       ▼               ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ PostgreSQL   │ │  Redis   │ │ External APIs│
│ (Data Store) │ │ (Cache)  │ │ - Apify      │
└──────────────┘ └────┬─────┘ │ - OpenAI     │
                      │       └──────────────┘
                      ▼
           ┌─────────────────────┐
           │  Background Workers │
           ├─────────────────────┤
           │ Dramatiq Workers    │
           │ APScheduler Tasks   │
           └─────────────────────┘
```

### Data Flow

```
User Input → API Validation → Business Logic → Database
                    ↓
            Async Tasks (Dramatiq)
                    ↓
            Scraping (Apify) → Data Normalization
                    ↓
            Snapshot Creation → Change Detection
                    ↓
            Alert Generation → Notifications
                    ↓
            AI Analysis (OpenAI) → Suggestions
```

---

## Tech Stack

### Backend

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | FastAPI 0.115+ | High-performance async web framework |
| **ORM** | SQLAlchemy 2.0+ | Async database operations |
| **Database** | PostgreSQL 16+ | Primary data storage |
| **Cache** | Redis 7.0+ | Caching & message broker |
| **Task Queue** | Dramatiq 1.18+ | Background job processing |
| **Scheduler** | APScheduler 3.10+ | Periodic task execution |
| **Migrations** | Alembic | Database schema versioning |
| **Validation** | Pydantic 2.0+ | Data validation & serialization |
| **Auth** | JWT (python-jose) | Secure token-based authentication |
| **Scraping** | Apify API | Amazon data extraction |
| **AI** | OpenAI API | Content optimization suggestions |
| **Monitoring** | Prometheus + Grafana | Metrics & visualization |
| **Error Tracking** | Sentry | Production error monitoring |
| **Package Manager** | uv | Ultra-fast Python dependency management |

### Frontend

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | React 18+ | UI library |
| **Build Tool** | Vite 5+ | Fast development & bundling |
| **Language** | TypeScript 5.0+ | Type-safe JavaScript |
| **Routing** | React Router DOM v6 | Client-side routing |
| **UI Components** | Radix UI + shadcn/ui | Accessible component library |
| **Styling** | Tailwind CSS 3+ | Utility-first CSS framework |
| **Forms** | React Hook Form | Form state management |
| **Charts** | Recharts | Data visualization |
| **HTTP Client** | Axios | API communication |
| **Rich Text** | Editor.js | Content editing |

### Infrastructure

| Category | Technology | Purpose |
|----------|-----------|---------|
| **IaC** | Terraform | AWS infrastructure provisioning |
| **Containers** | Docker + Docker Compose | Application containerization |
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Cloud Provider** | AWS (ECS Fargate, RDS, ElastiCache) | Production hosting |
| **Alternative Hosting** | Zeabur | Managed platform deployment |
| **Reverse Proxy** | Nginx / AWS ALB | Load balancing & SSL termination |

---

## Quick Start

### Prerequisites

```bash
# Required
- Python 3.11+
- Node.js 18.0+
- Docker 24.0+
- PostgreSQL 16+ (or Docker)
- Redis 7.0+ (or Docker)

# Optional (for production)
- AWS Account (for Terraform deployment)
- Apify API Token
- OpenAI API Key
```

### 1. Clone Repository

```bash
git clone https://github.com/RIDCorix/Amazcope.git
cd Amazcope
```

### 2. Backend Setup

```bash
cd backend

# Install uv (ultra-fast package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
cd src
uv run alembic upgrade head

# Start backend services with Docker Compose
cd ..
docker-compose up -d

# OR start services individually:
# Terminal 1: API Server
cd src
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Dramatiq Worker
uv run dramatiq core.dramatiq_app --processes 4 --threads 8

# Terminal 3: APScheduler (periodic tasks)
uv run python -m core.scheduler
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.local.example .env.local
# Edit with API URL (default: http://localhost:8000)

# Start development server
npm run dev
```

### 4. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)

---

## Development

### Environment Configuration

#### Backend `.env`

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=amazcope
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/amazcope

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-256-bit
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Monitoring (optional)
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx

# Environment
ENVIRONMENT=development
DEBUG=true
```

#### Frontend `.env.local`

```bash
VITE_API_URL=http://localhost:8000
NODE_ENV=development
```

### Database Migrations

```bash
cd backend/src

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest                          # Run all tests
uv run pytest --cov=src                # With coverage
uv run pytest -v                       # Verbose output
uv run pytest tests/test_api/          # Specific directory

# Frontend tests
cd frontend
npm test                               # Run all tests
npm run test:ci                        # CI mode with coverage
```

### Code Quality

```bash
# Backend linting & formatting
cd backend
uv run ruff check src/                 # Lint
uv run ruff check src/ --fix           # Auto-fix
uv run mypy src/                       # Type checking

# Frontend linting & formatting
cd frontend
npm run lint                           # ESLint
npm run lint:fix                       # Auto-fix
npm run format                         # Prettier
npm run type-check                     # TypeScript check
```

---

## Deployment

### Option 1: Zeabur (Recommended for Quick Deployment)

```bash
# 1. Setup GitHub Secrets
cd scripts
cp setup/.github.secrets.example .github.secrets
# Edit with your credentials
./setup-github-secrets.sh

# 2. Push to GitHub
git push origin main

# 3. Deploy via Zeabur Dashboard
# - Connect GitHub repository
# - Auto-deploys on push to main
# - Pre-configured with zeabur.json
```

### Option 2: AWS with Terraform

```bash
# 1. Configure AWS credentials
cd deployment/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit with your AWS settings

# 2. Initialize Terraform
terraform init

# 3. Plan deployment
terraform plan

# 4. Apply infrastructure
terraform apply

# 5. Outputs auto-sync to GitHub Secrets
# - DEPLOY_HOST
# - APP_URL
# - Database endpoints
```

### Option 3: Docker Compose (Self-Hosted)

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health/db

# Redis connectivity
curl http://localhost:8000/health/redis
```

---

## API Documentation

### Authentication

All API endpoints (except `/auth/login` and `/auth/register`) require JWT authentication:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password"}'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

# Use token in requests
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/v1/products
```

### Key Endpoints

#### Product Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tracking/products` | List all tracked products |
| POST | `/api/v1/tracking/products` | Add new product |
| GET | `/api/v1/tracking/products/{id}` | Get product details |
| PATCH | `/api/v1/tracking/products/{id}` | Update product |
| DELETE | `/api/v1/tracking/products/{id}` | Delete product |
| POST | `/api/v1/tracking/products/import-from-url` | Import from Amazon URL |
| POST | `/api/v1/tracking/products/{id}/refresh` | Force refresh product data |
| GET | `/api/v1/tracking/products/{id}/snapshots` | Get historical snapshots |
| GET | `/api/v1/tracking/products/{id}/alerts` | Get product alerts |

#### User Products (Ownership)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/user-products/claim` | Claim product ownership |
| DELETE | `/api/v1/user-products/{id}/unclaim` | Release ownership |
| GET | `/api/v1/user-products/owned` | List owned products |
| GET | `/api/v1/user-products/competitors` | List competitor products |

#### AI Suggestions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/suggestions` | List all suggestions |
| GET | `/api/v1/suggestions/{id}` | Get suggestion details |
| POST | `/api/v1/suggestions/{id}/review` | Approve/decline suggestion |
| DELETE | `/api/v1/suggestions/{id}` | Delete suggestion |
| GET | `/api/v1/suggestions/stats` | Get suggestion statistics |

#### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/metrics/summary` | Get metrics summary |
| GET | `/api/v1/metrics/comparison` | Compare multiple products |
| GET | `/api/v1/metrics/category-trend` | Get category trends |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Testing

### Test Coverage

Current test coverage: **49%** (Target: 75%+)

| Component | Coverage | Tests |
|-----------|----------|-------|
| Services Layer | 85%+ | 204 tests |
| API Endpoints | 30-40% | 37 tests |
| Overall | 49% | 241 tests |

### Running Tests

```bash
# Full test suite
cd backend
uv run pytest

# With coverage report
uv run pytest --cov=src --cov-report=html --cov-report=term

# Specific test file
uv run pytest tests/test_services/test_notification_service.py

# Watch mode (requires pytest-watch)
uv run ptw

# Frontend tests
cd frontend
npm test
```
