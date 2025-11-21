# Report Scheduler Platform

Multi-tenant report scheduling and delivery platform built with Python (FastAPI + Celery) backend and Vue 3 frontend on Azure infrastructure.

## ✅ Project Status

- ✅ **Backend**: Complete with Phase 3 + Future Enhancements (caching, burst protection, audit, incremental reports)
- ✅ **Frontend**: Complete with 5 production-ready views (Dashboard, Schedules, Executions, Reports, Gallery)
- ⏳ **Infrastructure**: Azure deployment ready (Terraform IaC)
- 📚 **Documentation**: Comprehensive implementation docs available

## Project Structure

```
ReportScheduler/
├── backend/           # Python FastAPI API + Celery workers
├── frontend/          # Vue 3 + TypeScript + Vuetify UI
├── infrastructure/    # Terraform IaC for Azure
├── docs/              # Architecture and design documentation
└── docker-compose.yml # Local development environment
```

## Quick Start (Local Development)

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 20+
- Poetry (Python dependency management)

### Start All Services

```bash
# Start backend, frontend, PostgreSQL, Redis, Azurite
docker-compose up

# Access services:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api-docs
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
@@### Option 2: Manual Setup (Recommended for Development)

@@#### 1. Start Infrastructure
@@```bash
@@docker-compose up -d postgres redis azurite
@@```

@@#### 2. Start Backend
```

### Backend Only

```bash
cd backend

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Run migrations
alembic upgrade head

@@# Start FastAPI server
@@poetry run uvicorn src.main:app --reload

@@# In a separate terminal, start Celery worker
@@poetry run celery -A src.workers.celery_app worker --loglevel=info
@@```

@@#### 3. Start Frontend
@@```bash
@@cd frontend

@@# Install dependencies (first time only)
@@npm install

@@# Create environment file
@@cat > .env.local << EOF
@@VITE_API_BASE_URL=http://localhost:8000
@@VITE_TENANT_ID=default-tenant
@@EOF

@@# Start development server
@@npm run dev
@@```

@@#### 4. Access Application
@@- **Frontend UI**: http://localhost:5173
@@- **Backend API Docs**: http://localhost:8000/docs
@@- **Health Check**: http://localhost:8000/api/v1/health

# Start API
uvicorn src.main:app --reload

# Start Celery worker (separate terminal)
celery -A src.workers.celery_app worker --loglevel=info

# Run tests
pytest tests/ -v
```

### Frontend Only

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Run tests
npm run test

# Build for production
npm run build
```

## Documentation

- **[requirements.md](docs/requirements.md)** - Original project requirements
- **[design.md](docs/design.md)** - System architecture and API specs
- **[code-guidelines.md](docs/code-guidelines.md)** - Coding standards and patterns
- **[plan.md](docs/plan.md)** - 16-week project plan with phases
- **[infrastructure.md](docs/infrastructure.md)** - Azure infrastructure details

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI (async, OpenAPI, type hints)
- **Task Queue**: Celery + Redis
- **Scheduler**: APScheduler (cron evaluation)
- **Database**: SQLAlchemy 2.0 + asyncpg (async PostgreSQL)
- **PDF Generation**: WeasyPrint (HTML → PDF)
- **Template Engine**: Liquid (liquidpy)
- **Testing**: pytest + pytest-asyncio

### Frontend
- **Framework**: Vue 3 with Composition API
- **Language**: TypeScript
- **State Management**: Pinia
- **Data Fetching**: VueQuery (TanStack Query)
- **Forms**: VeeValidate + Zod
- **UI Library**: Vuetify 3 (Material Design)
- **Build Tool**: Vite

### Infrastructure
- **Cloud**: Microsoft Azure
- **IaC**: Terraform
- **Compute**: Azure Container Apps with KEDA autoscaling
- **Database**: Azure Database for PostgreSQL Flexible Server
- **Cache**: Azure Cache for Redis Premium
- **Storage**: Azure Blob Storage (artifacts)
- **Messaging**: Azure Service Bus Premium
- **Observability**: Application Insights + Azure Monitor

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes**
   - Follow patterns in `docs/code-guidelines.md`
   - Write tests for new functionality
   - Run linters (`ruff` for Python, `eslint` for Vue)

3. **Test Locally**
   ```bash
   # Backend
   cd backend
   pytest tests/ --cov=src
   
   # Frontend
   cd frontend
   npm run test
   ```

4. **Create Pull Request**
   - CI will run tests, linting, security scans
   - Requires approval before merge

5. **Deploy**
   - Merge to `main` triggers deployment to dev
   - Staging requires manual approval
   - Production uses canary deployment (10% → 100%)

## Project Phases (16 Weeks)

- **Phase 1** (Weeks 1-2): Foundation - ✅ COMPLETE
- **Phase 2** (Weeks 3-5): Core Scheduling Engine
- **Phase 3** (Weeks 6-8): Report Generation Workers
- **Phase 4** (Weeks 9-10): Delivery & Email Notifications
- **Phase 5** (Weeks 11-12): Frontend UI & Artifact Gallery
- **Phase 6** (Weeks 13-14): Testing & Hardening
- **Phase 7** (Weeks 15-16): Deployment & Launch
- **Phase 8** (Post-launch): Iteration & Enhancements

See `docs/plan.md` for detailed milestones.

## License

Proprietary - Internal Use Only

## Support

For questions or issues, contact the platform team.
