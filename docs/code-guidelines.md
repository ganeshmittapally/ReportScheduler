# Code Guidelines

## 1. Purpose
Establish modern (2025) engineering standards for the Report Scheduler platform to ensure consistency, reliability, security, and ease of evolution. These guidelines apply across backend services, frontend/UI, infrastructure-as-code, data and ML components (if introduced).

## 2. Core Principles
- Clarity over cleverness; optimize for future readability.
- Strong typing where feasible (TypeScript, Python type hints, SQL schemas).
- Single Responsibility for modules, SOLID + clean architecture boundaries.
- Design for observability: logs, metrics, traces built-in.
- Secure-by-default: least privilege, validated inputs, encrypted secrets.
- API stability: version explicitly, avoid breaking changes without deprecation path.
- Automation first: repeatable builds, tests, deployments.

## 3. Repository & Branch Strategy
- Trunk-based preferred; short-lived feature branches (`feat/...`, `fix/...`, `chore/...`).
- Use Conventional Commits: `feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `test:`, `build:`, `ci:`, `chore:`, `revert:`.
- Pull Requests kept < 400 lines diff; large changes split.
- Require at least one review + passing CI (lint, tests, security scan) before merge.

## 4. Naming Conventions
- Classes / React Components / Types: PascalCase.
- Functions, variables: camelCase.
- Constants: UPPER_SNAKE_CASE.
- Async functions end with suffix `Async` if returning promises.
- Database tables: snake_case singular (`report_schedule`). Columns snake_case. Indices prefixed `idx_`.
- Environment variables: UPPER_SNAKE_CASE (`REPORT_DB_URL`).

## 5. Project Structure

### Backend (Node.js + TypeScript)
```
backend/
  src/
    api/                           # HTTP layer (controllers, middleware, routes)
      controllers/
        ReportController.ts        # Handles /reports endpoints
        ScheduleController.ts
        ExecutionController.ts
        ArtifactController.ts
      middleware/
        authMiddleware.ts          # JWT validation, tenant extraction
        errorHandler.ts            # Centralized error mapping
        rateLimiter.ts             # Per-tenant throttling
        requestLogger.ts           # Structured logging
      routes/
        index.ts                   # Route registry
        v1/                        # Versioned routes
          reportRoutes.ts
          scheduleRoutes.ts
      validators/
        reportSchemas.ts           # Zod/Joi schemas for input validation
    
    domain/                        # Business logic (framework-agnostic)
      models/
        ReportDefinition.ts        # Domain entities (pure classes)
        Schedule.ts
        ExecutionRun.ts
        Artifact.ts
      services/
        ReportService.ts           # Business operations
        ScheduleService.ts
        ExecutionService.ts
        DeliveryService.ts
      interfaces/
        IReportRepository.ts       # Port definitions (hexagonal)
        IStorageProvider.ts
        IDataSourceConnector.ts
      exceptions/
        DomainException.ts         # Custom error hierarchy
        ValidationException.ts
    
    infrastructure/                # External integrations
      database/
        PostgresReportRepository.ts  # Repository implementations
        migrations/                  # Flyway/Prisma migrations
        schema.sql
      storage/
        AzureBlobStorageProvider.ts
      queue/
        ServiceBusPublisher.ts
        ServiceBusConsumer.ts
      cache/
        RedisCache.ts
      connectors/
        SynapseConnector.ts
        RestApiConnector.ts
      
    workers/                       # Background job processors
      GenerationWorker.ts          # Consumes execution events
      DeliveryWorker.ts
      SchedulerWorker.ts           # Cron evaluation loop
    
    shared/                        # Cross-cutting utilities
      logger.ts                    # Structured logging (Winston/Pino)
      config.ts                    # Environment config loader
      telemetry.ts                 # OpenTelemetry setup
      constants.ts
      utils/
        dateUtils.ts
        cryptoUtils.ts
    
    templates/                     # Liquid template helpers
      filters/
        customFilters.ts           # Currency, percentage, etc.
      engine.ts                    # Liquid engine wrapper
    
  tests/
    unit/                          # Domain + service tests
      domain/
      services/
    integration/                   # Repository + API tests
      api/
      database/
    e2e/                          # Full workflow tests
      reportGeneration.test.ts
    fixtures/                      # Test data builders
    helpers/
  
  package.json
  tsconfig.json
  jest.config.js
  Dockerfile
  .env.example
```

**Key Patterns:**
- **Hexagonal Architecture**: Domain core isolated; infrastructure adapters pluggable.
- **Repository Pattern**: `IReportRepository` interface; Postgres/Mock implementations.
- **Service Layer**: Orchestrates domain logic; no HTTP concerns.
- **Dependency Injection**: Constructor injection; use `tsyringe` or manual factory.
- **DTOs**: Separate API request/response models from domain entities.

### Frontend (React + TypeScript)
```
frontend/
  src/
    components/                    # Reusable UI components
      common/
        Button/
          Button.tsx
          Button.module.css
          Button.test.tsx
        DataTable/
        Modal/
        LoadingSpinner/
      layout/
        Header/
        Sidebar/
        Footer/
      reports/
        ReportCard/               # Domain-specific components
        ReportForm/
        ReportPreview/
      schedules/
        ScheduleBuilder/          # Cron UI builder
        ScheduleList/
      executions/
        ExecutionTimeline/
        ExecutionLogs/
    
    features/                      # Feature-based modules
      reports/
        pages/
          ReportsPage.tsx
          ReportDetailPage.tsx
          CreateReportPage.tsx
        hooks/
          useReports.ts            # Data fetching hooks
          useReportMutations.ts
        api/
          reportApi.ts             # API client functions
        types/
          report.types.ts
    schedules/
      pages/
        SchedulesPage.tsx
        CreateSchedulePage.tsx   # Includes email delivery checkbox & recipient input
      hooks/
        useSchedules.ts
        useEmailConfig.ts         # Manage email template editing
      api/
        scheduleApi.ts
    executions/
      pages/
      hooks/
      api/
    gallery/                       # Artifact gallery feature
      pages/
        GalleryPage.tsx           # Main artifact listing with filters
        ArtifactDetailPage.tsx    # Preview, download, metadata view
      hooks/
        useArtifacts.ts           # Fetch artifacts with pagination & filters
        useArtifactPreview.ts     # Generate thumbnails & preview URLs
      api/
        artifactApi.ts
      components/
        ArtifactCard/             # Thumbnail, name, date, download button
        ArtifactFilters/          # Date range, report type, status filters
        PdfViewer/                # In-browser PDF viewer component    state/                         # State management
      store.ts                     # Redux store or Zustand
      slices/
        authSlice.ts
        reportsSlice.ts
      middleware/
        apiMiddleware.ts
    
    services/                      # Core services
      apiClient.ts                 # Axios instance with interceptors
      authService.ts               # Token management
      websocketService.ts          # Real-time updates (optional)
    
    hooks/                         # Shared custom hooks
      useAuth.ts
      usePagination.ts
      useDebounce.ts
      useWebSocket.ts
    
    utils/                         # Helper functions
      dateFormatters.ts
      validators.ts
      cronParser.ts
    
    types/                         # Shared TypeScript types
      api.types.ts
      domain.types.ts
    
    styles/
      global.css
      theme.ts                     # Material-UI or styled-components theme
      variables.css
    
    config/
      constants.ts
      routes.ts
    
  public/
    assets/
      icons/
      images/
  
  package.json
  tsconfig.json
  vite.config.ts (or webpack.config.js)
  .env.example
```

**Key Patterns:**
- **Feature-Sliced Design**: Group by feature, not layer (all report code together).
- **Component Composition**: Small, focused components; compose complex UIs.
- **Custom Hooks**: Encapsulate logic (data fetching, side effects).
- **State Management**: Redux Toolkit or Zustand for global state; React Query for server state.
- **API Layer Separation**: Centralized API client; feature-specific wrappers.

### Monorepo Structure (Optional)
```
root/
  packages/
    backend/              # Backend service
    frontend/             # React UI
    shared/               # Shared types & utilities
      types/
        domain.types.ts   # Shared between FE/BE
      utils/
        validation.ts
  infra/                  # Terraform modules
  docs/                   # Documentation
  scripts/                # Build & deployment scripts
  .github/
    workflows/
      ci.yml
  package.json            # Root workspace config (npm/yarn/pnpm workspaces)
  turbo.json              # Turborepo config (optional)
```

Keep layers decoupled: UI -> API -> Domain -> Persistence.## 6. Coding Style & Formatting
- Enforce formatters (Prettier, Black, gofmt) via pre-commit hooks.
- Max line length 100–120 char; wrap thoughtfully.
- Avoid nested conditionals >3 levels; refactor with guards / early returns.
- Do not leave commented-out code; remove or document rationale.

## 7. Documentation Practices
- Public functions & exported types get concise docstrings (purpose, params, returns, edge cases).
- Architectural decisions recorded in lightweight ADRs (`docs/adr/NNN-title.md`).
- Update `design.md` when introducing new component boundaries or protocols.

## 8. Error Handling & Resilience
- Use structured error objects (code, message, context). Never swallow exceptions silently.
- Prefer retry with exponential backoff for transient external failures; cap attempts.
- Circuit breakers or timeouts for external integrations (HTTP, DB, queue).
- Return user-safe messages externally; log internal diagnostic details.

## 9. Logging & Observability
- Use structured logging (JSON) with fields: `timestamp`, `level`, `service`, `traceId`, `spanId`.
- Levels: `DEBUG` (dev only), `INFO` (state change), `WARN` (recoverable anomaly), `ERROR` (failure), `FATAL` (shutdown).
- Correlate with distributed tracing (OpenTelemetry); emit spans around I/O and heavy compute.
- Emit key metrics: schedule latency, report generation duration, queue depth, error rate.

## 10. Performance & Scalability
- Profile hotspots (CPU, memory, I/O) before optimizing.
- Prefer streaming for large report payloads; avoid loading entire datasets in memory.
- Batch DB writes/reads; use pagination (cursor-based) for large queries.
- Cache immutable reference data; define clear TTL & invalidation strategy.
- Avoid N+1 queries; use JOINs or prefetch strategies.

## 11. Security
- Validate all external input (length, type, pattern, whitelist approach). Centralize validation schemas (e.g. Zod / Joi / Pydantic).
- Output encode when rendering HTML; never trust pre-sanitized content.
- Parameterized / prepared statements for DB queries only.
- Secrets managed via vault / key management service; never in source control.
- Use principle of least privilege for service accounts, DB roles.
- Enforce HTTPS/TLS; set secure cookies (HttpOnly, SameSite=strict where possible).
- Regular dependency scanning (Snyk, Dependabot) & supply chain integrity (checksum / signature verification).
- Address OWASP Top 10 (Injection, Auth failures, Sensitive Data Exposure, etc.) proactively.

## 12. API Design
- REST baseline; consider GraphQL only if complex aggregation requirements emerge.
- Consistent resource naming: `/reports`, `/schedules`, `/reports/{id}/runs`.
- Use standard response envelope only when necessary; otherwise return pure resource representations.
- Pagination fields: `items`, `nextCursor`.
- Provide idempotency keys for operations that create resources triggered by scheduling.
- Versioning: prefix `/v1/` and do additive evolution (never repurpose fields).

## 13. Data & Schema Management
- Use migrations (Liquibase, Flyway, Prisma, Alembic) version-controlled; no ad-hoc DDL in prod.
- Backfill scripts idempotent & logged.
- Prefer UUIDv7 or ULID for sortable unique IDs.
- Index only query-critical columns; monitor index bloat.

## 14. Testing Strategy
Testing Pyramid:
- Unit: fast, isolated (mock persistence, external services).
- Integration: real DB (ephemeral), verify module boundaries.
- Contract: provider/consumer tests for APIs & queue messages.
- E2E: minimal happy path + critical failure path.
Guidelines:
- Deterministic tests; avoid sleeps—use polling with timeouts.
- Coverage target ~80%; focus on business-critical paths > 90%.
- Use test data builders / factories; no magical constants.
- Snapshot tests only for stable large JSON outputs (reports) with semantic diff.

## 15. CI/CD & Automation
- Pipeline stages: lint → type-check → unit → integration → security scan → build artifact → deploy.
- Fail fast: linters & type-check gating early.
- Immutable artifacts (Docker images tagged with git SHA + semantic version).
- Deployment: blue-green or canary for backend; rollback script tested quarterly.
- Infrastructure changes reviewed + plan output attached to PR.

## 16. Dependency Management
- Pin versions; use minimal version bumps with changelog review.
- Remove unused dependencies quarterly.
- Prefer standard library or existing utilities over new deps (reduce attack surface).
- Track license compliance (no copyleft if conflicts with distribution goals).

## 17. Feature Flags
- Central flag service / config; flags must have: owner, expiry date, rollout plan.
- Remove stale flags within one sprint after full rollout.

## 18. Internationalization & Localization (If needed)
- Externalize user-visible strings; use keys not raw text.
- Date/number formatting via locale-aware libraries.

## 19. Accessibility (Frontend)
- Semantic HTML, ARIA only when necessary.
- Color contrast WCAG AA.
- Keyboard navigation for all interactive components.

## 20. AI/ML (Future Considerations)
- Data privacy: segregate PII before sending to external AI services.
- Prompt templates version-controlled; evaluate models with reproducible metrics.
- Human-in-the-loop review for generated reports (if any generative augmentation added).

## 21. Code Review Checklist
- Correctness: logic, edge cases, error paths.
- Clarity: names, structure, documentation present.
- Security: input validation, secret handling, auth checks.
- Performance: no obvious inefficiencies / N+1 / unbounded loops.
- Observability: logs/metrics added where new flows introduced.
- Tests: adequate coverage & quality (not superficial assertions).
- Dependencies: no unnecessary additions.
- Style: conforms to formatters & lint rules (should auto-pass).

## 22. Tooling Standards
- Linting: ESLint (TS), Ruff/Flake8 (Python), Checkstyle (Java) with CI enforcement.
- Static analysis: SonarQube / CodeQL nightly scan.
- Security: dependency scanning + secret scanning (Git hooks + CI).
- Pre-commit hooks: format, lint, secret scan.

## 23. Deprecation Policy
- Mark deprecated APIs with documentation note + warning log (throttled) for 1 minor version.
- Provide migration instructions and timeline (min 60 days) before removal.

## 24. Handling Large Reports
- Stream generation to temp storage (object store) before finalizing metadata in DB.
- Compress large ( >5MB ) CSV / JSON outputs (gzip).
- Provide asynchronous download flow with status endpoint.

## 25. Configuration Management
- Hierarchy: default config → environment overrides → runtime flags.
- All configuration schema validated at startup; fail fast on invalid.

## 26. Example Commit Message
```
feat(schedule): add idempotency key support to create endpoint

Allows clients retrying schedule creation to avoid duplicates.
Docs updated; integration tests added for key collision path.
```

## 27. Anti-Patterns to Avoid
- God objects / massive service classes.
- Implicit behavior via global mutable state.
- Overuse of inheritance; prefer composition.
- Silent catch blocks / TODO left unresolved in prod code.
- Mixing presentation and domain logic.

## 28. Periodic Hygiene Tasks
- Quarterly: dependency prune, flag cleanup, index usage audit.
- Monthly: review error budget & SLO adherence, update ADR list.

## 29. Future Evolution Notes
Track proposals in `docs/adr/` and link from `design.md` when accepted.

## 30. Quick Reference
- Formatting: run local formatter script `npm run format` / `black .` etc.
- Tests: `npm test` / `pytest -q` / `go test ./...` (depending on stack).
- Lint: `npm run lint` / `ruff check .`.

## 31. Domain-Specific Conventions (Report Scheduler)
### Scheduling
- Schedule evaluation functions must be pure & timezone-aware (IANA zones, no hardcoded offsets).
- Cron expressions validated at creation; use `cron-parser` or equivalent library.
- Next-fire calculation cached with TTL = time-to-next-evaluation.

### Execution & Idempotency
- Before starting execution, check for existing `execution_run` row with same `scheduleId` + `idempotencyKey`.
- Duplicate events (at-least-once delivery) must not create duplicate artifacts.
- `executionRunId` propagated through all logs/traces for correlation.

### Artifact Management
- Storage key format: `tenant/{tenantId}/run/{runId}/{artifactId}.{ext}`.
- Compress artifacts >5MB (gzip); store compression metadata.
- Lifecycle policies enforced at storage layer (auto-delete after retention period).

### Data Queries
- Enforce max row limit (configurable, default 100k) and timeout (60s) per report query.
- Use cursor-based pagination for large datasets; avoid OFFSET.
- Never allow arbitrary SQL; use parameterized query builders only.

### Email Delivery
- When schedule has `emailDelivery.enabled = true`, trigger email send after artifact creation.
- Email body must include signed URL to artifact (use Azure Blob SAS token with 7-day expiry).
- Email subject and body rendered via Liquid with variables: `reportName`, `executionDate`, `artifactUrl`, `galleryUrl`.
- Validate email addresses at schedule creation (regex + optional DNS MX check).
- Respect tenant email sending quotas; implement rate limiting per tenant.
- Track delivery receipts for audit trail.

### Artifact Gallery
- All artifacts immediately visible in frontend gallery upon creation (push via websocket or poll every 10s).
- Gallery supports filters: date range, report type, execution status, search by name.
- Signed URLs regenerated on-demand if expired (user clicks expired link \u2192 auto-renew \u2192 redirect).
- Thumbnail generation for PDFs (first page as PNG, max 200KB) for gallery preview.
- Deep linking: `/gallery?artifactId=xyz` pre-selects artifact in UI.

### Template Rendering
- Separate data preparation (business logic) from presentation (templates).
- Templates should be declarative; no embedded business logic or DB calls.
- Validate template syntax at upload; fail early with clear error messages.

### Delivery & Retries
- Classify errors: transient (429, 503, network timeout) vs permanent (401, 404, invalid recipient).
- Exponential backoff with jitter: base 2s, max 60s, cap 5 attempts.
- Dead-letter after max retries; manual review/replay process.

### Multi-Tenancy
- **CRITICAL**: Never omit `tenantId` filter in repository queries.
- Row-level security (RLS) policies in PostgreSQL enforced; test with dedicated isolation suite.
- Tenant context injected at API gateway; validated at every service boundary.

**Isolation Testing Requirements**:
```python
# tests/integration/test_tenant_isolation.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_cannot_access_other_tenant_reports(client: AsyncClient, tenant_a_token, tenant_b_token):
    """Verify tenant A cannot read tenant B's reports."""
    # Create report as tenant B
    response = await client.post(
        "/v1/reports",
        json={"name": "Tenant B Report", ...},
        headers={"Authorization": f"Bearer {tenant_b_token}"}
    )
    report_id = response.json()["id"]
    
    # Attempt to read as tenant A (should fail)
    response = await client.get(
        f"/v1/reports/{report_id}",
        headers={"Authorization": f"Bearer {tenant_a_token}"}
    )
    assert response.status_code == 404  # Not 403, to avoid info leak

@pytest.mark.asyncio
async def test_rls_enforces_tenant_boundary(db_session, tenant_a_id, tenant_b_id):
    """Verify PostgreSQL RLS blocks cross-tenant queries."""
    # Set session context to tenant A
    await db_session.execute(
        "SET LOCAL app.current_tenant_id = :tenant_id",
        {"tenant_id": tenant_a_id}
    )
    
    # Query should only return tenant A's data
    result = await db_session.execute(
        select(ReportDefinitionModel)
    )
    reports = result.scalars().all()
    
    assert all(r.tenant_id == tenant_a_id for r in reports)
    assert not any(r.tenant_id == tenant_b_id for r in reports)
```

### Auditing
- Log all destructive or security-sensitive actions: create/update/delete of definitions, schedules, delivery targets.
- Audit events include: `actor`, `action`, `entityType`, `entityId`, `before`/`after` diff.
- Audit table append-only; no updates/deletes.

### Time Handling
- All persisted timestamps in UTC; store as `timestamptz` in PostgreSQL.
- Convert to user timezone only at presentation layer (API response or UI).
- Use `DateTime` libraries (Luxon, date-fns) for timezone-aware operations.

### Large Payloads
- Stream generation output; never concatenate full report in memory.
- Use chunked encoding for HTTP responses; write-through to storage.
- Monitor memory usage per worker; alert if >80% sustained.

### Security
- Validate all schedule inputs: cron syntax, timezone, email addresses (regex + DNS MX check).
- Sanitize user-provided template content; escape HTML if rendering web previews.
- Rotate delivery credentials (SMTP, webhook tokens) via scheduled job.

### Performance Budgets
- Report generation: p50 <20s, p95 <60s, p99 <120s.
- Schedule trigger lag: p95 <5s from intended fire time.
- Delivery latency: p95 <30s post-generation.
- Measure against budgets in STAGE; gate PROD deployments on regression.

## 32. Backend Code Patterns

**Note**: Original examples were TypeScript/Node.js. Since stack decision is **Python + FastAPI**, key patterns translated below:

### FastAPI Endpoint Pattern (Python)
```python
# api/routes/reports.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from domain.services.report_service import ReportService
from api.dependencies import get_current_user, get_report_service
from domain.models.user import User

router = APIRouter(prefix="/v1/reports", tags=["reports"])

class CreateReportRequest(BaseModel):
    name: str
    description: Optional[str] = None
    query_spec: dict
    template_ref: str

class ReportResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    created_at: str
    
    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode)

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: CreateReportRequest,
    current_user: User = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Create a new report definition."""
    try:
        report = await report_service.create_report(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            dto=request
        )
        return ReportResponse.from_orm(report)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=dict)
async def list_reports(
    cursor: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service)
):
    """List reports with pagination."""
    result = await report_service.list_reports(
        tenant_id=current_user.tenant_id,
        cursor=cursor,
        limit=min(limit, 100)  # Cap at 100
    )
    return {
        "items": [ReportResponse.from_orm(r) for r in result.items],
        "next_cursor": result.next_cursor
    }
```

### Service Pattern (Python Domain Logic)
```python
# domain/services/report_service.py
from typing import Optional
from domain.models.report_definition import ReportDefinition
from domain.interfaces.report_repository import IReportRepository
from domain.exceptions import ValidationException
import logging

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo
    
    async def create_report(
        self, 
        tenant_id: str, 
        user_id: str, 
        dto: CreateReportRequest
    ) -> ReportDefinition:
        """Create and persist a report definition."""
        # Business validation
        if not self._validate_query_spec(dto.query_spec):
            raise ValidationException("Invalid query specification")
        
        # Domain entity creation
        report = ReportDefinition(
            tenant_id=tenant_id,
            created_by=user_id,
            name=dto.name,
            description=dto.description,
            query_spec=dto.query_spec,
            template_ref=dto.template_ref
        )
        
        # Persist
        saved = await self.report_repo.save(report)
        
        logger.info(
            "Report created",
            extra={
                "report_id": saved.id,
                "tenant_id": tenant_id,
                "user_id": user_id
            }
        )
        
        return saved
    
    def _validate_query_spec(self, spec: dict) -> bool:
        required_fields = ["data_source", "query"]
        return all(field in spec for field in required_fields)
```

### Repository Pattern (Python + SQLAlchemy)
```python
# infrastructure/database/postgres_report_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from domain.interfaces.report_repository import IReportRepository
from domain.models.report_definition import ReportDefinition
from infrastructure.database.models import ReportDefinitionModel

class PostgresReportRepository(IReportRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, report: ReportDefinition) -> ReportDefinition:
        """Insert new report into database."""
        model = ReportDefinitionModel(
            id=report.id,
            tenant_id=report.tenant_id,
            name=report.name,
            description=report.description,
            query_spec=report.query_spec,  # JSONB column
            template_ref=report.template_ref,
            created_at=report.created_at
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_entity(model)
    
    async def find_by_tenant_id(
        self, 
        tenant_id: str, 
        cursor: Optional[str] = None, 
        limit: int = 20
    ) -> tuple[list[ReportDefinition], Optional[str]]:
        """Paginated query filtered by tenant."""
        query = select(ReportDefinitionModel).where(
            ReportDefinitionModel.tenant_id == tenant_id
        )
        
        if cursor:
            query = query.where(ReportDefinitionModel.id > cursor)
        
        query = query.order_by(ReportDefinitionModel.id).limit(limit + 1)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        items = [self._to_entity(m) for m in models[:limit]]
        next_cursor = models[-1].id if len(models) > limit else None
        
        return items, next_cursor
    
    def _to_entity(self, model: ReportDefinitionModel) -> ReportDefinition:
        return ReportDefinition(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            description=model.description,
            query_spec=model.query_spec,
            template_ref=model.template_ref,
            created_at=model.created_at
        )
```

### Celery Worker Pattern (Python Background Jobs)
```python
# workers/generation_worker.py
from celery import Celery
from domain.services.execution_service import ExecutionService
from infrastructure.dependencies import get_execution_service
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    'reportscheduler',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task(bind=True, max_retries=5)
def execute_report_task(self, execution_id: str, report_id: str):
    """Celery task for report generation."""
    execution_service = get_execution_service()
    
    try:
        logger.info(f"Starting execution {execution_id}")
        execution_service.execute_report(execution_id, report_id)
        logger.info(f"Completed execution {execution_id}")
    except Exception as exc:
        logger.error(
            f"Execution {execution_id} failed: {exc}",
            exc_info=True
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

## 33. Python Package Structure
```typescript
// api/controllers/ReportController.ts
import { Request, Response, NextFunction } from 'express';
import { ReportService } from '../../domain/services/ReportService';
import { CreateReportDto } from '../validators/reportSchemas';

export class ReportController {
  constructor(private reportService: ReportService) {}

  async create(req: Request, res: Response, next: NextFunction) {
    try {
      const tenantId = req.user.tenantId; // From auth middleware
      const dto = req.body as CreateReportDto; // Validated by middleware
      
      const report = await this.reportService.createReport(tenantId, dto);
      
      res.status(201).json({
        data: report,
        meta: { createdAt: new Date().toISOString() }
      });
    } catch (error) {
      next(error); // Error middleware handles
    }
  }

  async list(req: Request, res: Response, next: NextFunction) {
    try {
      const tenantId = req.user.tenantId;
      const { cursor, limit = 20 } = req.query;
      
      const result = await this.reportService.listReports(
        tenantId, 
        { cursor: cursor as string, limit: Number(limit) }
      );
      
      res.json({
        items: result.items,
        nextCursor: result.nextCursor
      });
    } catch (error) {
      next(error);
    }
  }
}
```

### Service Pattern (Domain Logic)
```typescript
// domain/services/ReportService.ts
import { IReportRepository } from '../interfaces/IReportRepository';
import { IStorageProvider } from '../interfaces/IStorageProvider';
import { ReportDefinition } from '../models/ReportDefinition';
import { ValidationException } from '../exceptions/ValidationException';

export class ReportService {
  constructor(
    private reportRepo: IReportRepository,
    private storage: IStorageProvider,
    private logger: Logger
  ) {}

  async createReport(tenantId: string, dto: CreateReportDto): Promise<ReportDefinition> {
    // Business validation
    if (!this.isValidCronExpr(dto.schedule?.cronExpr)) {
      throw new ValidationException('Invalid cron expression');
    }

    // Domain entity creation
    const report = ReportDefinition.create({
      tenantId,
      name: dto.name,
      querySpec: dto.querySpec,
      templateRef: dto.templateRef
    });

    // Persist
    const saved = await this.reportRepo.save(report);
    
    this.logger.info('Report created', { 
      reportId: saved.id, 
      tenantId 
    });

    return saved;
  }

  private isValidCronExpr(expr?: string): boolean {
    // Use cron-parser library
    return true; // Simplified
  }
}
```

### Repository Pattern (Infrastructure)
```typescript
// infrastructure/database/PostgresReportRepository.ts
import { Pool } from 'pg';
import { IReportRepository } from '../../domain/interfaces/IReportRepository';
import { ReportDefinition } from '../../domain/models/ReportDefinition';

export class PostgresReportRepository implements IReportRepository {
  constructor(private pool: Pool) {}

  async save(report: ReportDefinition): Promise<ReportDefinition> {
    const query = `
      INSERT INTO report_definition (id, tenant_id, name, query_spec, template_ref, created_at)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *
    `;
    
    const result = await this.pool.query(query, [
      report.id,
      report.tenantId,
      report.name,
      JSON.stringify(report.querySpec),
      report.templateRef,
      report.createdAt
    ]);

    return this.mapToEntity(result.rows[0]);
  }

  async findByTenantId(tenantId: string, pagination: Pagination): Promise<PaginatedResult<ReportDefinition>> {
    const query = `
      SELECT * FROM report_definition
      WHERE tenant_id = $1 AND ($2::text IS NULL OR id > $2)
      ORDER BY id
      LIMIT $3
    `;
    
    const result = await this.pool.query(query, [
      tenantId,
      pagination.cursor || null,
      pagination.limit + 1 // Fetch one extra for nextCursor
    ]);

    const items = result.rows.slice(0, pagination.limit).map(this.mapToEntity);
    const nextCursor = result.rows.length > pagination.limit 
      ? result.rows[pagination.limit - 1].id 
      : null;

    return { items, nextCursor };
  }

  private mapToEntity(row: any): ReportDefinition {
    return new ReportDefinition(
      row.id,
      row.tenant_id,
      row.name,
      row.query_spec,
      row.template_ref,
      new Date(row.created_at)
    );
  }
}
```

### Worker Pattern (Background Processing)
```typescript
// workers/GenerationWorker.ts
import { ServiceBusConsumer } from '../infrastructure/queue/ServiceBusConsumer';
import { ExecutionService } from '../domain/services/ExecutionService';

export class GenerationWorker {
  constructor(
    private consumer: ServiceBusConsumer,
    private executionService: ExecutionService,
    private logger: Logger
  ) {}

  async start() {
    this.logger.info('GenerationWorker starting...');
    
    await this.consumer.subscribe('execution-requests', async (message) => {
      const { executionId, scheduleId, reportId } = message.body;
      
      try {
        await this.executionService.executeReport(executionId, reportId);
        await message.complete(); // Ack message
      } catch (error) {
        this.logger.error('Execution failed', { executionId, error });
        
        if (message.deliveryCount >= 5) {
          await message.deadLetter({ reason: 'Max retries exceeded' });
        } else {
          await message.abandon(); // Retry with backoff
        }
      }
    });
  }

  async stop() {
    await this.consumer.close();
    this.logger.info('GenerationWorker stopped');
  }
}
```

### Middleware Pattern (Cross-Cutting Concerns)
```typescript
// api/middleware/authMiddleware.ts
import { Request, Response, NextFunction } from 'express';
import { verify } from 'jsonwebtoken';

export const authMiddleware = async (
  req: Request, 
  res: Response, 
  next: NextFunction
) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ error: 'Missing token' });
    }

    const payload = verify(token, process.env.JWT_SECRET!) as JwtPayload;
    
    // Attach user context
    req.user = {
      userId: payload.sub,
      tenantId: payload.tenantId,
      roles: payload.roles
    };

    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' });
  }
};
```

## 33. Frontend Code Patterns

### Composable Pattern (Data Fetching with VueQuery)
```typescript
// composables/reports/useReports.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { reportApi } from '@/services/api/reports';
import type { Report, PaginatedResult } from '@/types/domain.types';
import { computed, ref, Ref } from 'vue';

export const useReports = (cursor?: Ref<string | undefined>) => {
  return useQuery({
    queryKey: ['reports', cursor],
    queryFn: () => reportApi.list({ cursor: cursor?.value, limit: 20 }),
    keepPreviousData: true,
    staleTime: 30000 // 30s
  });
};

export const useReportMutations = () => {
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: reportApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: reportApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    }
  });

  return { createMutation, deleteMutation };
};

// Alternative: Pure Vue composable without VueQuery
export const useReportsManual = () => {
  const reports = ref<Report[]>([]);
  const loading = ref(false);
  const error = ref<Error | null>(null);
  const cursor = ref<string | undefined>();

  const fetchReports = async () => {
    loading.value = true;
    error.value = null;
    try {
      const result = await reportApi.list({ cursor: cursor.value, limit: 20 });
      reports.value = result.items;
      cursor.value = result.nextCursor;
    } catch (e) {
      error.value = e as Error;
    } finally {
      loading.value = false;
    }
  };

  return { reports, loading, error, cursor, fetchReports };
};
```

### Component Pattern (Feature Component with Composition API)
```vue
<!-- views/reports/ReportsView.vue -->
<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useReports, useReportMutations } from '@/composables/reports/useReports';
import ReportCard from '@/components/reports/ReportCard.vue';
import Button from '@/components/common/Button.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';

const router = useRouter();
const cursor = ref<string | undefined>();
const { data, isLoading, error } = useReports(cursor);
const { createMutation } = useReportMutations();

const handleCreate = () => {
  router.push('/reports/create');
};

const handleLoadMore = () => {
  if (data.value?.nextCursor) {
    cursor.value = data.value.nextCursor;
  }
};
</script>

<template>
  <div class="reports-page">
    <LoadingSpinner v-if="isLoading" />
    
    <div v-else-if="error" class="error">
      Error loading reports: {{ error.message }}
    </div>

    <div v-else>
      <div class="header">
        <h1>Reports</h1>
        <Button @click="handleCreate">Create Report</Button>
      </div>

      <div class="reports-grid">
        <ReportCard
          v-for="report in data?.items"
          :key="report.id"
          :report="report"
        />
      </div>

      <Button
        v-if="data?.nextCursor"
        variant="secondary"
        @click="handleLoadMore"
      >
        Load More
      </Button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.reports-page {
  padding: 2rem;

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .reports-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }
}
</style>
```

### Artifact Gallery Component (Vue 3)
```vue
<!-- views/gallery/GalleryView.vue -->
<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { useArtifacts } from '@/composables/gallery/useArtifacts';
import ArtifactCard from '@/components/gallery/ArtifactCard.vue';
import ArtifactFilters from '@/components/gallery/ArtifactFilters.vue';
import Button from '@/components/common/Button.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';

const filters = reactive({
  startDate: null as Date | null,
  endDate: null as Date | null,
  reportId: null as string | null,
  status: 'all'
});

const cursor = ref<string | undefined>();
const { data, isLoading, refetch } = useArtifacts({ ...filters, cursor });

const handleFilterChange = (newFilters: typeof filters) => {
  Object.assign(filters, newFilters);
  cursor.value = undefined; // Reset pagination
  refetch();
};

const handleDownload = (signedUrl: string) => {
  window.open(signedUrl, '_blank');
};

const handleLoadMore = () => {
  if (data.value?.nextCursor) {
    cursor.value = data.value.nextCursor;
  }
};
</script>

<template>
  <div class="gallery-page">
    <div class="header">
      <h1>Report Gallery</h1>
      <ArtifactFilters
        :filters="filters"
        @update:filters="handleFilterChange"
      />
    </div>

    <LoadingSpinner v-if="isLoading" />

    <div v-else class="artifacts-grid">
      <ArtifactCard
        v-for="artifact in data?.items"
        :key="artifact.id"
        :artifact="artifact"
        @download="handleDownload(artifact.signedUrl)"
      />
    </div>

    <Button
      v-if="data?.nextCursor"
      @click="handleLoadMore"
      class="load-more-btn"
    >
      Load More
    </Button>
  </div>
</template>

<style scoped lang="scss">
.gallery-page {
  padding: 2rem;

  .header {
    margin-bottom: 2rem;

    h1 {
      margin-bottom: 1rem;
    }
  }

  .artifacts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .load-more-btn {
    display: block;
    margin: 0 auto;
  }
}
</style>
```

### Schedule Form with Email Delivery (Vue 3)
```vue
<!-- components/schedules/ScheduleForm.vue -->
<script setup lang="ts">
import { ref, computed, reactive } from 'vue';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

const scheduleSchema = toTypedSchema(
  z.object({
    reportId: z.string().uuid(),
    cronExpr: z.string(),
    timezone: z.string(),
    emailDelivery: z.object({
      enabled: z.boolean(),
      recipients: z.array(z.string().email()).min(1).optional(),
      subjectTemplate: z.string().optional(),
      bodyTemplate: z.string().optional(),
      attachPdf: z.boolean().optional()
    })
  })
);

const emit = defineEmits<{
  submit: [data: any]
}>();

const { handleSubmit, defineField, values } = useForm({
  validationSchema: scheduleSchema,
  initialValues: {
    emailDelivery: {
      enabled: false,
      recipients: [],
      subjectTemplate: '{{reportName}} - {{executionDate}}',
      bodyTemplate: 'Your report is ready. <a href="{{artifactUrl}}">View Report</a>',
      attachPdf: false
    }
  }
});

const [reportId] = defineField('reportId');
const [cronExpr] = defineField('cronExpr');
const [timezone] = defineField('timezone');
const [emailEnabled] = defineField('emailDelivery.enabled');
const [recipients] = defineField('emailDelivery.recipients');
const [subjectTemplate] = defineField('emailDelivery.subjectTemplate');
const [bodyTemplate] = defineField('emailDelivery.bodyTemplate');
const [attachPdf] = defineField('emailDelivery.attachPdf');

const onSubmit = handleSubmit((values) => {
  emit('submit', values);
});
</script>

<template>
  <form @submit="onSubmit" class="schedule-form">
    <!-- Report, Cron & Timezone fields -->
    
    <div class="email-section">
      <div class="form-group">
        <label class="checkbox-label">
          <input v-model="emailEnabled" type="checkbox" />
          Send email when report is ready
        </label>
      </div>

      <template v-if="emailEnabled">
        <div class="form-group">
          <label for="recipients">Recipients (comma-separated)</label>
          <input
            id="recipients"
            v-model="recipients"
            type="text"
            placeholder="user@example.com, team@example.com"
          />
        </div>

        <div class="form-group">
          <label for="subject">Email Subject Template</label>
          <input
            id="subject"
            v-model="subjectTemplate"
            type="text"
          />
          <small class="help-text">
            Available: {{'{{'}}reportName{'}}'}, {{'{{'}}executionDate{'}}'}
          </small>
        </div>

        <div class="form-group">
          <label for="body">Email Body Template</label>
          <textarea
            id="body"
            v-model="bodyTemplate"
            rows="5"
          />
          <small class="help-text">
            Available: {{'{{'}}artifactUrl{'}}'}, {{'{{'}}galleryUrl{'}}'}
          </small>
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="attachPdf" type="checkbox" />
            Attach PDF to email (if file &lt; 10MB)
          </label>
        </div>
      </template>
    </div>

    <button type="submit" class="btn-primary">
      Save Schedule
    </button>
  </form>
</template>

<style scoped lang="scss">
.schedule-form {
  max-width: 600px;

  .email-section {
    margin-top: 2rem;
    padding: 1.5rem;
    background: #f7fafc;
    border-radius: 8px;
  }

  .form-group {
    margin-bottom: 1.5rem;

    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 600;
    }

    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: normal;
    }

    input[type="text"],
    textarea {
      width: 100%;
      padding: 0.5rem;
      border: 1px solid #cbd5e0;
      border-radius: 4px;
    }

    .help-text {
      display: block;
      margin-top: 0.25rem;
      color: #718096;
      font-size: 0.875rem;
    }
  }

  .btn-primary {
    width: 100%;
    margin-top: 1rem;
  }
}
</style>
```

### API Client Pattern (Centralized HTTP)
```typescript
// services/apiClient.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import { authService } from './authService';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor - attach auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = authService.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          authService.logout();
          window.location.href = '/login';
        }
        return Promise.reject(this.normalizeError(error));
      }
    );
  }

  private normalizeError(error: AxiosError): AppError {
    return {
      code: error.response?.data?.code || 'UNKNOWN_ERROR',
      message: error.response?.data?.message || error.message,
      status: error.response?.status
    };
  }

  get<T>(url: string, config?: any) {
    return this.client.get<T>(url, config).then(res => res.data);
  }

  post<T>(url: string, data?: any, config?: any) {
    return this.client.post<T>(url, data, config).then(res => res.data);
  }

  put<T>(url: string, data?: any, config?: any) {
    return this.client.put<T>(url, data, config).then(res => res.data);
  }

  delete<T>(url: string, config?: any) {
    return this.client.delete<T>(url, config).then(res => res.data);
  }
}

export const apiClient = new ApiClient();
```

### State Management Pattern (Pinia Store)
```typescript
// stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authService } from '@/services/auth';
import type { User, LoginCredentials } from '@/types/domain.types';

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);

  // Getters
  const isAuthenticated = computed(() => !!token.value);
  const userRole = computed(() => user.value?.role);

  // Actions
  const login = async (credentials: LoginCredentials) => {
    const response = await authService.login(credentials);
    user.value = response.user;
    token.value = response.token;
    localStorage.setItem('auth_token', response.token);
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    localStorage.removeItem('auth_token');
  };

  const initAuth = () => {
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      token.value = savedToken;
    }
  };

  return { user, token, isAuthenticated, userRole, login, logout, initAuth };
}, {
  persist: true
});
```

### Form Pattern (VeeValidate + Zod) - Report Form
```vue
<!-- components/reports/ReportForm.vue -->
<script setup lang="ts">
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

const reportSchema = toTypedSchema(
  z.object({
    name: z.string().min(3).max(100),
    description: z.string().optional(),
    querySpec: z.object({
      dataSource: z.string(),
      query: z.string().min(10)
    }),
    scheduleExpr: z.string().regex(/^(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)\s+(\*|[0-9,\-*/]+)$/)
  })
);

const emit = defineEmits<{
  submit: [data: any]
}>();

const { handleSubmit, defineField, errors } = useForm({
  validationSchema: reportSchema
});

const [name, nameAttrs] = defineField('name');
const [description, descriptionAttrs] = defineField('description');
const [dataSource, dataSourceAttrs] = defineField('querySpec.dataSource');
const [query, queryAttrs] = defineField('querySpec.query');
const [scheduleExpr, scheduleExprAttrs] = defineField('scheduleExpr');

const onSubmit = handleSubmit((values) => {
  emit('submit', values);
});
</script>

<template>
  <form @submit="onSubmit">
    <div class="form-group">
      <label for="name">Report Name</label>
      <input
        id="name"
        v-model="name"
        v-bind="nameAttrs"
        type="text"
      />
      <span v-if="errors.name" class="error">{{ errors.name }}</span>
    </div>

    <div class="form-group">
      <label for="dataSource">Data Source</label>
      <select
        id="dataSource"
        v-model="dataSource"
        v-bind="dataSourceAttrs"
      >
        <option value="synapse">Azure Synapse</option>
        <option value="sql">Azure SQL</option>
      </select>
    </div>

    <div class="form-group">
      <label for="query">SQL Query</label>
      <textarea
        id="query"
        v-model="query"
        v-bind="queryAttrs"
        rows="10"
      />
      <span v-if="errors['querySpec.query']" class="error">
        {{ errors['querySpec.query'] }}
      </span>
    </div>

    <div class="form-group">
      <label for="schedule">Schedule (Cron)</label>
      <input
        id="schedule"
        v-model="scheduleExpr"
        v-bind="scheduleExprAttrs"
        type="text"
        placeholder="0 9 * * *"
      />
      <span v-if="errors.scheduleExpr" class="error">
        {{ errors.scheduleExpr }}
      </span>
    </div>

    <button type="submit" class="btn-primary">
      Create Report
    </button>
  </form>
</template>

<style scoped lang="scss">
.form-group {
  margin-bottom: 1.5rem;

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
  }

  input, select, textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .error {
    color: #e53e3e;
    font-size: 0.875rem;
    margin-top: 0.25rem;
  }
}
</style>
```

## 34. Glossary
- **ExecutionRun**: single attempt to produce artifacts from a schedule trigger.
- **Artifact**: output file (PDF/CSV/JSON) with retention policy.
- **DeliveryReceipt**: record of sending artifact to external channel.
- **Schedule Trigger Lag**: actual trigger time minus intended cron time.
- **Idempotency Key**: unique identifier preventing duplicate executions.
- **Dead-Letter Queue (DLQ)**: storage for messages that failed processing after max retries.
- **Repository Pattern**: abstraction layer between domain and data access.
- **Hexagonal Architecture**: domain core isolated from external dependencies.
- **DTO (Data Transfer Object)**: object for transferring data between layers.

---
This document is living; propose changes via PR referencing rationale (performance, reliability, security, developer experience).
