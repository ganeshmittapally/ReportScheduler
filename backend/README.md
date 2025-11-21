# Report Scheduler Backend

Python 3.11+ backend service using FastAPI, Celery, and SQLAlchemy.

## Quick Start

```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A src.workers.celery_app worker --loglevel=info

# Start scheduler loop (separate terminal)
python -m src.scheduler.scheduler_loop
```

## Project Structure

```
backend/
├── src/
│   ├── api/              # FastAPI routes and dependencies
│   ├── domain/           # Business logic and domain models
│   ├── infrastructure/   # Database, storage, messaging implementations
│   ├── workers/          # Celery background tasks
│   ├── scheduler/        # APScheduler cron evaluation loop
│   └── main.py           # FastAPI application entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/              # Database migrations
├── templates/            # Liquid templates for reports and emails
└── pyproject.toml        # Poetry dependencies
```

## Development

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Type checking
mypy src/ --strict

# Linting
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Security scan
bandit -r src/ -ll
```

## Docker

```bash
# Build API image
docker build -t reportscheduler-api:latest .

# Build worker image
docker build -t reportscheduler-worker:latest -f Dockerfile.worker .

# Run with Docker Compose (includes PostgreSQL, Redis, Azurite)
docker-compose up
```

## Environment Variables

See `.env.example` for required configuration.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Blob Storage
- `JWT_SECRET`: Secret key for JWT validation
- `ENVIRONMENT`: dev/staging/production
