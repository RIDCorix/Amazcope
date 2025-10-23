# Amazcope Setup Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Database Setup](#4-database-setup)
  - [5. Environment Configuration](#5-environment-configuration)
- [Running the Application](#running-the-application)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required

- **Node.js 18+** - Frontend runtime
  ```bash
  node --version  # Should show v18 or higher
  ```

- **Docker & Docker Compose 24+** - For database services
  ```bash
  docker --version
  ```

- **uv** - Ultra-fast Python package installer
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## Quick Start

For the impatient developer who wants to get up and running in 5 minutes:

```bash
# 1. Clone the repository
git clone <repository-url> amazcope
cd amazcope

# 2. Start infrastructure services (PostgreSQL, Redis, etc.)
cd deps
docker compose up -d
cd ..

# 3. Setup backend
cd backend
cp .env.example .env
# Edit .env with your credentials (see section below)
uv sync
cd src
uv run aerich upgrade
cd ../..

# 4. Setup frontend
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local to point to your backend API
cd ..

# 5. Start services (in separate terminals)
# Terminal 1: Backend API
cd backend/src
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Dramatiq Worker
cd backend/src
uv run dramatiq core.dramatiq_app products.tasks --processes 2 --threads 4

# Terminal 3: APScheduler (periodic tasks)
cd backend/src
uv run python -m core.scheduler

# Terminal 4: Frontend
cd frontend
npm run dev

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

---

## Detailed Setup

### 1. Clone Repository

```bash
git clone <repository-url> amazcope
cd amazcope
```

**Verify structure:**
```bash
ls -la
# Should see: backend/, frontend/, deps/, docs/, scripts/, etc.
```

---

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (faster than pip)
uv sync

# Verify installation
uv run python --version
```

#### Create Environment File

```bash
cp .env.example .env
```

**Edit `.env` with your configuration:**

```env
# Database Configuration (Supabase or Local PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=amazcope
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password@localhost:5432/amazcope

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Task Queue Configuration (Dramatiq)
# Dramatiq uses Redis as broker, configured via REDIS_URL above

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
APIFY_API_TOKEN=your-apify-token-here
OPENAI_API_KEY=sk-your-openai-api-key-here

# Application Settings
DEBUG=True
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Monitoring (Optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

#### Initialize Database

```bash
cd src

# Run database migrations
uv run aerich upgrade

# OR if starting fresh
uv run aerich init-db
```

#### Create Admin User

```bash
# Using CLI tool
uv run cli.py create-user

# Follow prompts to create admin user
```

---

### 3. Frontend Setup

#### Install Node Dependencies

```bash
cd frontend
npm install
```

#### Create Environment File

```bash
cp .env.local.example .env.local
```

**Edit `.env.local`:**

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application Settings
NODE_ENV=development
NEXT_PUBLIC_APP_NAME=Amazcope
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_SENTRY=false
```

---

### 4. Database Setup

#### Option A: Using Docker Compose (Recommended)

```bash
cd deps

# Start all infrastructure services
docker compose up -d

# Verify services are running
docker compose ps

# View logs
docker compose logs -f
```

**Services started:**
- PostgreSQL (port 5432)
- Redis (port 6379)
- pgAdmin (port 5050) - Optional web UI for PostgreSQL

#### Option B: Local PostgreSQL Installation

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Create database:**
```bash
psql -U postgres
CREATE DATABASE amazcope;
CREATE USER amazcope_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE amazcope TO amazcope_user;
\q
```

#### Option C: Supabase (Cloud Database)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Get connection string from Settings > Database
4. Update `DATABASE_URL` in backend `.env`

---

### 5. Environment Configuration

#### Required External Services

**1. Apify (Amazon Scraping)**

- Sign up at [apify.com](https://apify.com)
- Get API token from Settings > Integrations
- Add to backend `.env`: `APIFY_API_TOKEN=your-token`

**2. OpenAI (AI Optimization)**

- Get API key from [platform.openai.com](https://platform.openai.com)
- Add to backend `.env`: `OPENAI_API_KEY=sk-your-key`

**3. Sentry (Error Tracking - Optional)**

- Sign up at [sentry.io](https://sentry.io)
- Create project
- Get DSN from Settings
- Add to backend `.env`: `SENTRY_DSN=your-dsn`

---

## Running the Application

### Development Mode

## VSCode Workflow
To streamline development, use the provided VSCode tasks:
```
cp .vscode/tasks.json.example .vscode/tasks.json
cp .vscode/launch.json.example .vscode/launch.json
```
These tasks are automatically set up to start backend, frontend, and other services on folderOpen with a single command. If you want to restart all services, you can also use `Reload Window` (Cmd/Ctrl + Shift + P).

#### Manual Start (Multiple Terminals)

**Terminal 1: Infrastructure Services**
```bash
cd deps
docker compose up
```

**Terminal 2: Backend API**
```bash
cd backend/src
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3: Dramatiq Worker**
```bash
cd backend/src
uv run dramatiq core.dramatiq_app products.tasks --processes 2 --threads 4
```

**Terminal 4: APScheduler (Periodic Tasks)**
```bash
cd backend/src
uv run python -m core.scheduler
```

**Terminal 5: Frontend****
```bash
cd frontend
npm run dev
```

### Using Docker Compose (Full Stack)

```bash
cd backend
docker compose up -d
```

This starts all services in containers.

### Access Points

Once running, access:

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Redoc**: http://localhost:8000/redoc
- **Prometheus**: http://localhost:9090 (if configured)
- **Grafana**: http://localhost:3001 (if configured)
- **pgAdmin**: http://localhost:5050 (if using Docker)

---

## Development Workflow

### Backend Development

#### Hot Reload

API server auto-reloads on code changes with `--reload` flag.

#### Database Migrations

**Create migration after model changes:**
```bash
cd backend/src
uv run aerich migrate --name "add_new_feature"
```

**Apply migrations:**
```bash
uv run aerich upgrade
```

**Rollback migration:**
```bash
uv run aerich downgrade
```

**View migration history:**
```bash
uv run aerich history
```

#### Code Quality

**Linting:**
```bash
cd backend
uv run ruff check src/
uv run ruff check src/ --fix  # Auto-fix
```

**Type checking:**
```bash
uv run mypy src/
```

**Format code:**
```bash
uv run ruff format src/
```

#### Generate Product History
Under normal circumstances, product history is generated automatically via scheduled tasks daily. To manually generate history for all products, run:
```bash
uv run cli.py generate-product-history
```

### Frontend Development

#### Hot Reload

Next.js automatically reloads on changes.

#### Code Quality

**Linting:**
```bash
cd frontend
npm run lint
npm run lint:fix  # Auto-fix
```

**Type checking:**
```bash
npm run type-check
```

**Format code:**
```bash
npm run format
```

### Adding New Dependencies

**Backend:**
```bash
cd backend
# Edit pyproject.toml [dependencies] section
uv sync
```

**Frontend:**
```bash
cd frontend
npm install <package-name>
```

---

## Testing

### Backend Tests

**Run all tests:**
```bash
cd backend
uv run pytest
```

**Run with coverage:**
```bash
uv run pytest --cov=src --cov-report=html
```

**Run specific test file:**
```bash
uv run pytest tests/test_api/test_users.py
```

**Run specific test:**
```bash
uv run pytest tests/test_api/test_users.py::test_create_user
```

**Verbose output:**
```bash
uv run pytest -v
```

**View coverage report:**
```bash
open htmlcov/index.html
```

### Frontend Tests

**Run all tests:**
```bash
cd frontend
npm test
```

**Run with coverage:**
```bash
npm run test:ci
```

**Watch mode:**
```bash
npm run test:watch
```

### Integration Tests

```bash
# Start all services first
cd backend
docker compose up -d

# Run integration tests
uv run pytest tests/integration/
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Symptom:**
```
sqlalchemy.exc.OperationalError: (asyncpg.exceptions.InvalidCatalogNameError)
```

**Solution:**
```bash
# Ensure PostgreSQL is running
docker compose ps

# Check database exists
docker compose exec postgres psql -U postgres -l

# Create database if needed
docker compose exec postgres psql -U postgres -c "CREATE DATABASE amazcope;"
```

#### 2. Redis Connection Error

**Symptom:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Check Redis is running
docker compose ps redis

# Restart Redis
docker compose restart redis

# Check Redis logs
docker compose logs redis
```

#### 3. Dramatiq Tasks Not Running

**Symptom:**
Tasks not executing or workers not processing jobs

**Solution:**
```bash
# Check worker is running
ps aux | grep dramatiq

# Restart worker
pkill -f dramatiq
cd backend/src
uv run dramatiq core.dramatiq_app products.tasks --processes 2 --threads 4

# Check worker logs for errors
# Workers will log to stdout/stderr
```

#### 4. Frontend Cannot Connect to Backend

**Symptom:**
```
Network Error / CORS Error
```

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify CORS origins in backend/.env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Restart backend API
```

#### 5. Module Not Found Errors

**Backend:**
```bash
cd backend
rm -rf .venv
uv sync
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 6. Database Migration Conflicts

**Solution:**
```bash
cd backend/src

# View current migration state
uv run aerich history

# Rollback to previous
uv run aerich downgrade

# Nuclear option: Reset database (⚠️ destroys all data)
docker compose down -v
docker compose up -d postgres
uv run aerich init-db
```

#### 7. Port Already in Use

**Solution:**
```bash
# Find process using port
lsof -ti:8000  # Backend
lsof -ti:3000  # Frontend
lsof -ti:5432  # PostgreSQL

# Kill process
kill -9 $(lsof -ti:8000)

# Or use different port
uvicorn main:app --port 8001
```

### Debugging Tips

**Enable debug logging:**
```bash
# Backend
cd backend/src
export LOG_LEVEL=DEBUG
uv run uvicorn main:app --reload --log-level debug

# Frontend
cd frontend
export NODE_ENV=development
npm run dev
```


**Check Dramatiq worker status:**
```bash
cd backend/src
# Workers will show task processing in stdout logs
# Use ps to verify workers are running
ps aux | grep dramatiq
```
---
### External Services

- **FastAPI**: https://fastapi.tiangolo.com
- **Next.js**: https://nextjs.org/docs
- **Tortoise ORM**: https://tortoise.github.io
- **Dramatiq**: https://dramatiq.io
- **Apify**: https://docs.apify.com

### Monitoring

**Prometheus + Grafana Setup:**
```bash
# In backend/docker-compose.yml, services are pre-configured
cd devops/
docker compose up -d
cp terraform.tfvars.example terraform.tfvars
# fill in terraform.tfvars with your desired configurations
terraform -var-file=terraform.tfvars apply -auto-approve

# Access:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```
###
---

**Happy tracking!** 🚀
