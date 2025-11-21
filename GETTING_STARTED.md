# 🚀 Getting Started - Report Scheduler

## ✅ Installation Complete!

**What's Been Installed:**
- ✅ Python 3.11.9
- ✅ pip 24.0
- ✅ Poetry 2.2.1 (dependency manager)
- ✅ Docker Desktop 4.52.0
- ✅ All 80+ Python dependencies (FastAPI, SQLAlchemy, Celery, pytest, etc.)
- ✅ Virtual environment at `.venv`
- ✅ `.env` configuration file

## 🎯 Next Steps to Start the Application

### Step 1: Launch Docker Desktop

Docker Desktop has been installed but needs to be started:

**Option A - Start from Start Menu:**
1. Press `Windows Key`
2. Type "Docker Desktop"
3. Click to launch
4. Wait for Docker to start (whale icon in system tray will stop animating)

**Option B - Start from Command:**
```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Step 2: Start the Application

Once Docker Desktop is running, start all services:

```powershell
# Navigate to project root (if not already there)
cd C:\Users\prasu\OneDrive\Public\Projects\ReportScheduler

# Start all services
docker compose up
```

This will start:
- **PostgreSQL** (database) on port 5432
- **Redis** (cache/queue) on port 6379
- **Azurite** (Azure Storage emulator) on port 10000
- **Backend API** on port 8000
- **Celery Worker** (background tasks)
- **Frontend** on port 5173

### Step 3: Access the Application

Once all containers are running:

- **API Documentation**: http://localhost:8000/api-docs
- **API Health Check**: http://localhost:8000/health
- **Frontend** (when implemented): http://localhost:5173

### Step 4: Test the Schedule API

Create a schedule:
```powershell
$body = @{
    report_definition_id = "report-123"
    name = "Daily Sales Report"
    cron_expression = "0 9 * * *"
    timezone = "America/New_York"
    email_delivery_config = @{
        recipients = @("team@example.com")
        subject = "Daily Sales Report"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/schedules" -Method Post -Body $body -ContentType "application/json"
```

Preview a cron expression:
```powershell
$body = @{
    cron_expression = "0 9 * * *"
    timezone = "America/New_York"
    count = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/schedules/cron/preview" -Method Post -Body $body -ContentType "application/json"
```

## 🛠️ Development Commands

### Backend Development

```powershell
cd backend

# Run tests
poetry run pytest

# Run linter
poetry run ruff check .

# Format code
poetry run ruff format .

# Type checking
poetry run mypy src

# Database migration (create new)
poetry run alembic revision --autogenerate -m "description"

# Database migration (apply)
poetry run alembic upgrade head

# Start API only (without Docker)
poetry run uvicorn src.main:app --reload
```

### Docker Commands

```powershell
# Start all services
docker compose up

# Start in background
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f api

# Rebuild containers
docker compose up --build

# Remove all containers and volumes
docker compose down -v
```

## 📊 Database Access

Once Docker is running, you can connect to PostgreSQL:

**Connection Details:**
- Host: `localhost`
- Port: `5432`
- Database: `reportscheduler`
- Username: `reportuser`
- Password: `reportpass`

**Using psql:**
```powershell
docker compose exec postgres psql -U reportuser -d reportscheduler
```

## 🐛 Troubleshooting

### Docker Desktop Won't Start
- Ensure WSL 2 is installed (Docker Desktop will prompt if needed)
- Try restarting your computer
- Check Windows Services: "Docker Desktop Service" should be running

### Port Already in Use
If ports 5432, 6379, 8000, or 5173 are already in use:
```powershell
# Find process using port (example: 8000)
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <PID> /F
```

### Container Fails to Start
```powershell
# View detailed logs
docker compose logs api

# Rebuild container
docker compose up --build api
```

### Database Migration Issues
```powershell
# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d postgres
docker compose exec api poetry run alembic upgrade head
```

## 📁 Project Structure

```
ReportScheduler/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── api/               # API routes and schemas
│   │   ├── domain/            # Business logic and interfaces
│   │   ├── infrastructure/    # Database, external services
│   │   ├── scheduler/         # APScheduler loop
│   │   └── utils/             # Utilities (cron validation)
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Unit and integration tests
│   ├── .env                   # Environment variables
│   └── pyproject.toml         # Python dependencies
├── frontend/                   # Vue 3 frontend (Phase 1)
├── infrastructure/             # Terraform IaC (future)
├── docs/                       # Documentation
└── docker-compose.yml          # Local development stack
```

## 🎯 Current Phase: Phase 2 Complete

✅ **Completed:**
- Project scaffolding
- Database models (7 tables)
- Schedule CRUD API (8 endpoints)
- APScheduler loop
- Cron validation utilities
- Repository and service layers

📝 **Next: Phase 3 - Report Generation**
- Celery worker implementation
- Azure Synapse query execution
- Liquid template rendering
- PDF generation with WeasyPrint
- Azure Blob Storage integration

## 🔗 Useful Links

- **API Documentation**: http://localhost:8000/api-docs (when running)
- **Design Documentation**: `docs/design.md`
- **Code Guidelines**: `docs/code-guidelines.md`
- **Infrastructure**: `docs/infrastructure.md`
- **Implementation Plan**: `docs/plan.md`
- **Phase 2 Summary**: `PHASE2_COMPLETE.md`

---

**Ready to start!** Launch Docker Desktop, then run `docker compose up` to start developing! 🚀
