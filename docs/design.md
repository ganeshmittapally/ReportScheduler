# System Design

## 1. Overview
The Report Scheduler system automates the generation, formatting, and distribution of analytical reports (CSV, PDF, HTML, JSON) on recurring or event-driven schedules. Core goals: reliability of delivery, extensibility of report definitions, multi-channel distribution (email, web download, webhook, Slack), and cost-efficient scaling.

## 2. High-Level Architecture
Event‑driven, service‑oriented architecture composed of:
- API Gateway / Backend Service (REST) – CRUD for reports, schedules, templates, delivery targets, audit querying.
- Scheduler Service – Maintains schedule registry (cron, interval, calendar rules, ad-hoc triggers) and emits execution events.
- Report Generation Workers – Stateless pool consuming execution events; run data extraction + rendering pipeline.
### Template & Rendering Engine – Liquid templates with custom filters; HTML intermediate → PDF via Puppeteer. CSV generation direct from query results.
- Delivery Service – Routes finalized artifacts to channels (Email, S3 link, Slack, Webhook, FTP).
- Metadata & Audit Store – Persists schedule definitions, run status, error logs, delivery receipts.
- Object Storage – Holds generated artifacts (versioned, encrypted, lifecycle policies).
- Queue / Event Bus – Decouples scheduling from generation & delivery (e.g., Kafka topic or SQS + SNS fan-out).
- Observability Stack – Central logging, tracing, metrics (OpenTelemetry + Prometheus + Grafana).

```
Client/UI -> API Service -> (DB)                
			 |                          
		 Scheduler Service --(events)--> Queue/Bus --> Generation Workers --> Object Store
									 |                         |         
									 \--> Delivery Service ----+--> Channels (Email/Slack/Webhook)
```

## 3. Core Domain Concepts
- ReportDefinition: query spec, data sources, transformation pipeline, template, output formats.
- Schedule: cron/interval/calendar + timezone + idempotency key + optional email delivery config (recipients, subject template, body template).
- ExecutionRun: one attempt; tracks status (queued, running, succeeded, failed, aborted), metrics.
- Artifact: generated file asset with metadata (hash, size, format, retention expiry, signed URL for web access).
- DeliveryTarget: channel settings (address, webhook URL, Slack channel, credentials ref).
- DeliveryReceipt: outcome record (success/failure, timestamp, latency, retry count).
- ArtifactGallery: UI view showing all generated reports per tenant with filters (date, status, report type), preview, download.

## 4. Components Detail
### Frontend
SPA or modular UI consuming REST APIs. Provides:
- **Schedule Builder**: Cron UI + optional email delivery checkbox with recipient management (comma-separated emails, validation).
- **Artifact Gallery**: Paginated view of all generated reports with thumbnail previews (for PDFs), download buttons, filter by date/report/status.
- **Report Preview**: In-browser PDF viewer or CSV preview.
- **Run History**: Execution timeline with status, duration, error logs.
- **Delivery Configuration**: Manage email templates (subject, body with variable substitution).
- **Error Diagnostics**: Detailed failure reasons with suggested fixes.

### Backend API Service
Responsibilities: authentication & authorization, input validation, business orchestration, idempotent creation, versioned APIs, rate limiting. Exposes endpoints for definitions, schedules, executions (status), artifacts, delivery targets, audit search.

**Rate Limiting Implementation**:
- Per-tenant rate limits stored in Redis: `{tenantId}:api:requests` counter with TTL.
- Limits: 100 req/min (Standard tier), 500 req/min (Premium), 2000 req/min (Enterprise).
- Algorithm: Token bucket or sliding window via Redis sorted sets.
- Response: HTTP 429 with `Retry-After` header when exceeded.

**Quota Management**:
- Per-tenant quotas: max schedules (Standard: 50, Premium: 500, Enterprise: unlimited), max executions/day (Standard: 1000, Premium: 10k, Enterprise: custom).
- Enforcement: Check before schedule creation; block execution if daily quota reached.
- Alerting: Notify tenant admin at 80% quota usage via email.

### Scheduler Service
Maintains in-memory + persistent schedule registry. Uses distributed locking (e.g., Redis Redlock or DB advisory locks) to avoid duplicate triggers. Emits ExecutionRequested events with correlation IDs.

### Generation Workers
Consume events from Service Bus; fetch definition & schedule context; perform:
1. **Data Extraction**: Connect to Azure Synapse via ODBC/JDBC; execute parameterized SQL with timeout (60s default).
2. **Transformation**: Apply data mapping, aggregations, filtering (TypeScript functions).
3. **Rendering**: Pass data to Liquid template engine; generate HTML intermediate.
4. **PDF Conversion**: Puppeteer renders HTML to PDF with custom headers/footers, page breaks.
5. **Storage Upload**: Stream PDF to Blob Storage; compute checksum; record metadata.

**Scaling**: Container Apps autoscale on Service Bus queue depth (target: 10 msgs per instance) with max 300 instances. Each worker processes 1 execution at a time; concurrency via horizontal scaling.

### Delivery Service
Queues delivery tasks; executes with retry/backoff; handles channel-specific formatting (multipart email, Slack blocks, webhook JSON schema). Emits DeliveryResult events.

### Data Layer
Primary relational DB for strong consistency of schedules & run states. Object storage (S3/Azure Blob/GCS) for artifacts. Optional Redis for caching frequently accessed definitions & recent run statuses.

### Eventing
Kafka (topic partitioning by scheduleId) or AWS combination (SQS for work queue + SNS for fan-out). Dead-letter queue for failures after max retry.

## 5. Data Flow
1. User creates ReportDefinition & Schedule via UI/API; optionally enables email delivery with recipient list.
2. Scheduler calculates next fire time & publishes ExecutionRequested event.
3. Worker pulls event, loads definition, executes data query pipeline.
4. Worker streams generated content to Object Storage; writes metadata record with signed URL (7-day expiry, renewable).
5. **Artifact record immediately visible in frontend gallery** (websocket notification or polling).
6. If email enabled on schedule: Worker posts DeliveryRequested event with artifact ID.
7. Delivery Service composes email with:
   - Subject: rendered from template (e.g., "{{reportName}} - {{date}}")
   - Body: HTML template with **direct link** to artifact (signed URL) + optional inline preview
   - Attachment: option to attach PDF directly or link-only (configurable per tenant for size limits)
8. Delivery Service sends email via Azure Communication Services (SMTP); stores DeliveryReceipt.
9. User clicks email link → redirects to frontend gallery with artifact pre-selected → download or view in-browser.
10. Observability: each stage emits logs, metrics, traces.

## 6. Security Design

### Authentication Implementation
- **Provider**: Azure AD B2C (OAuth2/OIDC) for tenant user authentication.
- **Flow**: Authorization code flow with PKCE for frontend; client credentials for service-to-service.
- **Tokens**: JWT access tokens (5-min expiry), refresh tokens (7-day expiry with rotation).
- **Token validation**: Verify signature via Azure AD public keys (JWKS endpoint), validate issuer, audience, expiry.
- **API Gateway**: Middleware validates Bearer token on every request; extracts userId + tenantId from claims.

### Authorization Model
- **Roles**: `tenant_admin`, `report_creator`, `viewer` (stored in Azure AD app roles or custom claims).
- **Permissions**:
  - `tenant_admin`: Full CRUD on all tenant resources.
  - `report_creator`: Create/edit own reports & schedules, view all tenant artifacts.
  - `viewer`: Read-only access to reports, schedules, artifacts.
- **Resource Ownership**: Reports/schedules have `created_by` field; creators can edit/delete own resources.
- **Enforcement**: Backend checks role + ownership before mutation operations; read operations filtered by tenantId.

### Multi-Tenancy Isolation
- **Database**: tenantId field on all top-level entities; PostgreSQL Row-Level Security (RLS) policies enforce isolation.
- **Storage**: Blob containers per tenant OR shared container with path prefix `tenant/{tenantId}/`.
- **Testing**: Automated tests verify cross-tenant data leakage impossible (inject different tenantId, expect 403/404).

### Data Encryption
- **In-transit**: TLS 1.2+ enforced; HTTPS only.
- **At-rest**: Azure Storage SSE with customer-managed keys (CMK) in Key Vault; PostgreSQL TDE enabled.
- **Secrets**: Azure Key Vault for SMTP credentials, webhook tokens, API keys; accessed via Managed Identity.
- **PII**: Email addresses hashed in logs; report data never logged.

### Audit Trail
- **Table**: `audit_event` (append-only, no updates/deletes).
- **Events**: create/update/delete of reports, schedules, delivery targets; execution failures; access to sensitive endpoints.
- **Retention**: 1 year in PostgreSQL; archive to Blob Storage for longer compliance periods.
- **Export**: API endpoint for compliance (`GET /audit-events?startDate=&endDate=`) with admin role required.

### Input Validation
- **Schema validation**: Pydantic models for FastAPI; reject unknown fields (strict mode).
- **SQL injection**: Parameterized queries only via SQLAlchemy; no raw SQL with user input.
- **XSS**: Output encoding in email templates; CSP headers in frontend.
- **SSRF**: Whitelist data source URLs; block internal IP ranges (169.254.0.0/16, 10.0.0.0/8) in webhook targets.

## 7. Scalability Considerations
- Stateless workers enabling autoscaling based on queue depth & processing latency.
- Partitioned topics to distribute load; ensure ordering only where needed (per schedule, not globally).
- Use read replicas for heavy analytical queries separate from write workload.
- Shard large artifact metadata if table growth impacts index efficiency.
- Caching: schedule next-fire computations and definition objects; invalidate on update.
- Backpressure: enforce max concurrent executions per tenant; queue overflow alerts.

## 8. Technology Stack (Finalized)

### Backend: Python 3.11+
- **API Framework**: FastAPI (async, OpenAPI auto-generation, type hints with Pydantic)
- **Task Queue**: Celery + Redis broker (mature, proven at >1M tasks/day)
- **Scheduler Loop**: APScheduler (cron expression evaluation, timezone support)
- **ORM**: SQLAlchemy 2.0 (async support via asyncpg driver)
- **Migrations**: Alembic (version control for schema changes)
- **Template Engine**: Liquid (via liquidpy for Liquid template syntax)
- **PDF Generation**: WeasyPrint (HTML→PDF with CSS Paged Media support)
- **HTTP Client**: httpx (async HTTP for data source queries)
- **Validation**: Pydantic v2 (request/response models, configuration)
- **Testing**: pytest + pytest-asyncio + httpx.AsyncClient

### Frontend: Vue 3 + TypeScript
- **Framework**: Vue 3 with Composition API (`<script setup>` syntax)
- **State Management**: Pinia (Vue 3 official store)
- **Data Fetching**: VueQuery (TanStack Query for Vue)
- **Form Validation**: VeeValidate + Zod schemas
- **UI Library**: Vuetify 3 or Element Plus (Material Design)
- **HTTP Client**: Axios (configured with interceptors)
- **Build Tool**: Vite (fast HMR, optimized builds)
- **Testing**: Vitest (unit) + Playwright (E2E)

### Infrastructure
- **Database**: Azure Database for PostgreSQL Flexible Server (row-level security, JSONB for flexible metadata)
- **Data Warehouse**: Azure Synapse Analytics (serverless SQL pool) for report data sources
- **Cache**: Azure Cache for Redis Premium (distributed locks, rate limiting, session storage)
- **Storage**: Azure Blob Storage (Hot/Cool tiers, lifecycle policies)
- **Messaging**: Azure Service Bus Premium (topics/subscriptions, dead-letter queues)
- **Container Platform**: Azure Container Apps with KEDA (event-driven autoscaling)
- **IaC**: Terraform with Azure provider
- **CI/CD**: Azure DevOps Pipelines or GitHub Actions
- **Observability**: Application Insights, Azure Monitor, OpenTelemetry SDK
- Object Storage: Azure Blob Storage (Hot/Cool tiers with lifecycle management).
- Queue/Event: Azure Service Bus Premium (topics/subscriptions with dead-letter queues).
- Cache/Locking: Azure Cache for Redis Premium (clustering + persistence for distributed locks).
- Template Engine: Liquid (Shopify template language - rich features, secure sandboxing, extensive filters).
- PDF Rendering: Puppeteer (Headless Chromium) in container; alternative: Azure Functions with Playwright.
- CI/CD: Azure DevOps Pipelines or GitHub Actions with Azure integration.
- Observability: Application Insights, Azure Monitor, Log Analytics, OpenTelemetry SDK.
- IaC: Terraform with Azure provider.

## 9. API Design
Versioned base path `/v1/`. Representative endpoints:

**Reports & Schedules**
- `POST /reports` create definition.
- `GET /reports/{id}` retrieve.
- `POST /schedules` attach schedule to report with optional email config:
  ```json
  {
    "reportId": "uuid",
    "cronExpr": "0 9 * * *",
    "timezone": "America/New_York",
    "emailDelivery": {
      "enabled": true,
      "recipients": ["user@example.com", "team@example.com"],
      "subjectTemplate": "{{reportName}} - {{executionDate}}",
      "bodyTemplate": "Your report is ready. <a href='{{artifactUrl}}'>View Report</a>",
      "attachPdf": false
    }
  }
  ```
- `PUT /schedules/{id}` update schedule including email settings.

**Executions & Artifacts**
- `GET /runs?reportId=&status=&cursor=` list executions.
- `POST /runs/{id}/retry` idempotent retry.
- `GET /artifacts?tenantId=&reportId=&startDate=&endDate=&cursor=` **artifact gallery listing** with filters.
- `GET /artifacts/{id}` retrieve artifact metadata + generate signed URL (7-day expiry).
- `GET /artifacts/{id}/download` proxy download with access logging.
- `GET /artifacts/{id}/preview` return thumbnail or first page for PDFs.
- `POST /artifacts/{id}/renew-url` extend signed URL expiry (authenticated users only).

**Delivery**
- `POST /delivery-targets` configure channel.
- `GET /delivery-receipts?artifactId=` get delivery history for artifact.

**Health & Metadata**
- `GET /health` liveness probe (200 if API responds).
- `GET /health/ready` readiness probe (200 if DB + Redis + Service Bus reachable).
- `GET /metrics` Prometheus metrics endpoint (auth required).
- `GET /api-docs` OpenAPI spec (auto-generated by FastAPI).

**API Standards**:
- **Pagination**: Cursor-based via `cursor` query param + `nextCursor` in response. Limit: default 20, max 100.
- **Error Format**: 
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Invalid cron expression",
      "details": { "field": "cronExpr", "value": "invalid" },
      "requestId": "uuid",
      "timestamp": "2025-11-21T10:30:00Z"
    }
  }
  ```
- **Versioning Strategy**: URL-based (`/v1/`, `/v2/`). Deprecation: mark v1 deprecated with `Sunset` header 6 months before removal. Maintain v1 + v2 concurrently for transition period.
- **Rate Limit Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` on every response.
- **Idempotency**: Support `Idempotency-Key` header for POST/PUT/DELETE; store key + response hash in Redis (24h TTL); return cached response if duplicate.

## 10. Database Schema (Sketch)
Tables (simplified):
- `tenant`(id, name, status)
- `report_definition`(id, tenant_id, name, query_spec JSONB, template_ref, active, created_at)
- `schedule`(id, report_id, cron_expr, timezone, next_run_at, paused, last_evaluated_at, **email_delivery_config JSONB**, updated_at)
  - email_delivery_config structure: `{enabled: bool, recipients: string[], subjectTemplate: string, bodyTemplate: string, attachPdf: bool}`
- `execution_run`(id, schedule_id, status, started_at, completed_at, duration_ms, worker_id, error_code, artifact_id, attempt)
- `artifact`(id, execution_run_id, tenant_id, report_id, storage_key, **signed_url TEXT, url_expires_at TIMESTAMPTZ**, format, bytes, checksum, thumbnail_key TEXT, expires_at, created_at)
- `delivery_target`(id, tenant_id, type, config JSONB, active)
- `delivery_receipt`(id, artifact_id, target_id, status, attempts, sent_at, latency_ms, error_message)
- `audit_event`(id, tenant_id, actor_id, action, entity_type, entity_id, timestamp, diff JSONB)

Indexes:
- Composite on (`schedule_id`, `status`), partial for active schedules.
- Hash index for artifact checksum.
- **`artifact` table**: index on (`tenant_id`, `created_at` DESC) for gallery queries, index on (`report_id`, `created_at` DESC).
- **`artifact` table**: index on `url_expires_at` for cleanup job (expired URL regeneration).

## 11. Reliability & Resilience
- At-least-once delivery of execution events; idempotent worker processing (check existing run status).
- Retry transient failures with capped exponential backoff (e.g., 5 attempts).
- Graceful shutdown: workers finish current job before termination; heartbeat for liveness.
- DLQ monitoring with automated alerting & manual replay process.

## 12. Observability Strategy

### Metrics (Prometheus format via Application Insights)
**Scheduler Metrics**:
- `scheduler_scan_duration_seconds` (histogram): Time to scan for due schedules.
- `scheduler_next_fire_lag_seconds` (histogram): Actual trigger time - intended time.
- `schedules_evaluated_total` (counter): Total schedules checked per loop.
- `schedules_triggered_total` (counter): Schedules that fired.

**Execution Metrics**:
- `report_generation_duration_seconds{report_type, status}` (histogram): Time to generate report.
- `execution_failures_total{reason}` (counter): Failures by reason (timeout, data_error, permission_denied).
- `artifact_size_bytes{format}` (histogram): Generated file sizes.
- `concurrent_executions` (gauge): Active worker tasks.

**Delivery Metrics**:
- `delivery_latency_seconds{channel}` (histogram): Time from artifact ready to sent.
- `delivery_attempts_total{channel, status}` (counter): Success/failure by channel.
- `email_bounce_rate` (gauge): Percentage of bounced emails.

**Infrastructure Metrics**:
- `database_connection_pool_usage` (gauge): Active connections / pool size.
- `service_bus_queue_depth{queue}` (gauge): Messages waiting.
- `redis_memory_usage_bytes` (gauge): Memory consumption.
- `api_request_duration_seconds{endpoint, method, status}` (histogram): API latency.

### Structured Logging (JSON to Application Insights)
**Required Fields**: `timestamp`, `level`, `service`, `tenantId`, `traceId`, `spanId`, `userId`, `message`.
**Levels**: DEBUG (dev only), INFO (state changes), WARN (recoverable), ERROR (failures), CRITICAL (service down).
**Context**: Include `scheduleId`, `executionId`, `artifactId` when applicable.
**No PII**: Hash email addresses, never log query results or report data.

### Dashboards (Azure Workbooks)
1. **Executive Dashboard**: Active tenants, daily executions, success rate, p95 generation time, cost per execution.
2. **Operations Dashboard**: Queue depth over time, scheduler lag, worker utilization, error rate by type.
3. **Performance Dashboard**: API p50/p95/p99 latency, database query performance, slow queries (>1s).
4. **Tenant Health**: Per-tenant execution success rate, quota usage, failed deliveries.

### Alerts (Azure Monitor → PagerDuty)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| High failure rate | >5% failed executions in 15 min | P2 | Investigate logs, check data source connectivity |
| Scheduler lag | p95 lag >30s for 10 min | P2 | Check scheduler service, Redis locks |
| Queue backlog | Service Bus depth >1000 msgs for 10 min | P3 | Scale workers, check for stuck jobs |
| Database saturation | Connection pool >90% for 5 min | P2 | Scale up or add read replicas |
| API latency spike | p95 >2s for 5 min | P3 | Check slow queries, scale API instances |
| Service down | Health check failing >2 min | P1 | Immediate page, check service logs |
| Disk space low | Blob storage >80% quota | P3 | Review retention policies, clean up old artifacts |
| Email delivery failure | >10% bounce rate in 1 hour | P3 | Check SMTP config, review recipient lists |

### Tracing (OpenTelemetry)
- Spans: API request → Scheduler trigger → Worker execution → Delivery.
- Trace ID propagated via Service Bus message metadata.
- Slow traces (>5s) sampled at 100%; normal traces at 10%.

## 13. Security & Compliance
Implement periodic rotating credentials, vulnerability scanning (container & dependency), secret scanning in CI. Provide audit export endpoints for compliance (CSV/JSON). Support data retention policies with artifact lifecycle expiration.

## 14. Performance Targets (Scale: 1000+ tenants, 50k schedules, 300 concurrent)
- Median generation time < 20s for standard reports (target workload: 10k rows, single chart PDF).
- p95 generation time < 45s; p99 < 90s.
- p95 schedule trigger latency < 10s from intended fire time.
- p99 delivery completion < 60s post generation.
- Error rate < 2% (excluding user data errors or invalid queries).
- Service Bus processing throughput: > 50 msgs/sec sustained.
- Worker cold start latency: < 5s (Container Apps).
- Database connection pool: 50 connections per API instance; PgBouncer pooling for workers.
- Redis cache hit rate: > 80% for schedule definitions & next-fire times.

## 15. Extensibility

### Data Source Plugins
Interface: `IDataSource { connect(), query(sql, params), disconnect() }`.
- **Built-in**: Azure Synapse, Azure SQL, REST API connector.
- **Future**: Cosmos DB aggregation, Azure Data Explorer (Kusto), Fabric lakehouse.
- Registration: metadata table `data_source_connector` with connection string template & auth method.

### Template Features (Liquid)
Custom filters for domain-specific formatting:
- `currency`: `{{ value | currency: 'USD' }}`
- `percentage`: `{{ ratio | percentage: 2 }}`
- `chart_url`: Generate Azure Charts API URLs for embedding.
- `format_date`: Timezone-aware date formatting.

**Email Template Variables** (available in subjectTemplate & bodyTemplate):
- `{{reportName}}`: Report definition name.
- `{{executionDate}}`: Execution timestamp formatted per tenant timezone.
- `{{artifactUrl}}`: Signed URL to artifact (7-day validity).
- `{{tenantName}}`: Tenant display name.
- `{{galleryUrl}}`: Deep link to frontend gallery with artifact pre-selected.
- `{{downloadUrl}}`: Direct download endpoint (tracked).

### Delivery Channel Plugins
Interface: `IDeliveryChannel { send(artifact, target, metadata) }`.
- **Built-in**: SMTP email, Webhook POST, Blob Storage direct link.
- **Planned**: Slack, Microsoft Teams, SFTP, Azure Event Grid.
- Configuration via `delivery_target.config` JSONB field.

## 16. Risk & Mitigation (Design Focus)
- Heavy long-running queries → enforce query timeouts + pre-aggregation.
- Large artifact storage growth → lifecycle policies + compression.
- Duplicate executions due to race conditions → distributed lock + idempotency checks.
- Tenant data leakage risk → rigorous RLS policies + integration tests verifying isolation.

## 17. Future Evolution
- Support real-time (event-triggered) reports via webhook ingestion.
- Introduce GraphQL overlay for complex client aggregation.
- Add ML summarization for large CSV outputs (opt-in) with privacy guardrails.
- **Enhanced Gallery Features**: 
  - Full-text search within artifact metadata.
  - Bulk download (zip multiple artifacts).
  - Artifact versioning/comparison UI.
  - Sharing artifacts with external users (time-limited public links).
  - Commenting/annotations on artifacts.
- **Email Enhancements**:
  - Rich HTML email templates with embedded charts/tables (not just links).
  - Per-recipient customization (personalized data slices).
  - Email open tracking & link click analytics.

## 18. Finalized Decisions

### Worker Architecture
**Decision**: Azure Container Apps with KEDA autoscaling (serverless containers).
- Scales to zero during idle; cold start <3s acceptable for async workload.
- No hard timeout limits (unlike Azure Functions 10-min cap).
- Supports long-running PDF generation (up to 30 min if needed).

### Multi-Region Strategy
**Decision**: Active-Active across 3 regions initially.
- **Regions**: US East, EU West, Asia Southeast.
- **Data Strategy**: 
  - Schedule metadata replicated read-only to all regions via Azure Cosmos DB (PostgreSQL API) for global distribution.
  - Primary PostgreSQL per region for execution runs & audit (region-local writes).
  - Blob Storage with geo-redundant replication (GRS).
  - Traffic Manager routes users to nearest region based on latency.
- **Schedule Distribution**: Geo-pinned (schedule fires in tenant's assigned region); cross-region failover only.

### Artifact Retention
**Decision**: 30 days default (Hot storage), configurable per tenant up to 365 days.
- Lifecycle policy: Hot → Cool (30d) → delete (or archive to separate container if regulatory).

### SLA Tiers
| Tier | Trigger SLA | Generation p95 | Delivery | Retention | Support | Price Indicator |
|------|-------------|----------------|----------|-----------|---------|----------------|
| **Standard** | 99% < 30s lag | < 60s | Best effort | 30d | Email, 48h | Base |
| **Premium** | 99.5% < 10s lag | < 30s | Guaranteed retry | 90d | Priority, 4h | 3x Base |
| **Enterprise** | 99.9% < 5s lag | < 20s | Guaranteed + alerts | Custom (up to 365d) | Dedicated, 1h | 10x Base |

### Data Sources
**Primary**: Azure Synapse Analytics (serverless SQL pool or dedicated pool).
**Secondary**: Direct Azure SQL Database connections, REST API connectors (authenticated via Managed Identity or API keys in Key Vault).
**Query Interface**: Parameterized SQL templates stored with report definitions; no arbitrary SQL execution.

### Template Engine
**Decision**: Liquid (liquidjs library for Node.js).
- Sandboxed execution; no arbitrary code.
- Rich filter library (date formatting, number formatting, string manipulation, conditionals, loops).
- Custom filters for business logic (currency conversion, aggregation helpers).
- Security: strict mode enabled; no file system access.

### Scale Parameters (Initial Launch)
- **Tenants**: 1,000+ (targeting 5,000 within Year 1).
- **Schedules per tenant**: Average 50 (range 10-200).
- **Total schedules**: ~50,000 active.
- **Peak concurrent executions**: 300.
- **Average execution duration**: 20s (p50), 45s (p95).
- **Daily execution volume**: ~15,000 runs (assuming mixed hourly/daily schedules).

### Capacity Planning
- Worker pool: 300 Container App instances max (1 vCPU, 2GB RAM each).
- Service Bus: Premium tier (1 messaging unit = 1,000 msg/sec; scale to 2-4 units).
- PostgreSQL: GP_Gen5_8 (8 vCores) per region with read replicas.
- Redis: Premium P2 (6GB) per region for caching & locking.
- Blob Storage: 5TB initial (avg artifact 2MB; 30d retention; ~75k artifacts).
- Synapse: Serverless SQL pool (pay-per-query) or DW500c dedicated.

---
This design will iterate; updates tracked through ADRs and versioned sections above.

## Appendix A: Architecture Decision Records (ADRs)

### ADR Template
```markdown
# ADR-NNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## Context
What is the issue we're facing? What forces are at play?

## Decision
What decision did we make?

## Consequences
What are the trade-offs? What becomes easier/harder?

## Alternatives Considered
What other options did we evaluate?
```

### ADR-001: Backend Language - Python vs Node.js/TypeScript

**Status**: Accepted (2025-11-21)

**Context**:
- Requirements.md specified Python + Azure.
- Initial design.md used TypeScript/Node.js for backend.
- Need to finalize before implementation.

**Decision**:
Use **Python 3.11+ with FastAPI** for backend services.

**Rationale**:
1. Aligns with original requirements.md.
2. Strong Azure SDK support (azure-identity, azure-storage-blob, azure-servicebus).
3. Excellent data processing libraries for Synapse integration (pandas, pyodbc, sqlalchemy).
4. FastAPI provides async performance comparable to Node.js.
5. Team familiarity per requirements context.

**Consequences**:
- **Positive**: Unified data stack, rich PDF generation libraries (reportlab, weasyprint), mature async ecosystem.
- **Negative**: No shared language with Vue 3 frontend (requires separate type definitions); slightly higher cold start vs Node.js for serverless.

**Alternatives Considered**:
- TypeScript/Node.js: Better frontend alignment, but weaker data science ecosystem.
- Go: Best performance, but steeper learning curve and limited Azure SDK maturity.

### ADR-002: Frontend Framework - Vue 3 vs React vs Angular

**Status**: Accepted (2025-11-21)

**Context**:
- Requirements.md mentioned Angular.
- User requested Vue 3 instead.

**Decision**:
Use **Vue 3 with Composition API + TypeScript**.

**Rationale**:
1. User preference over Angular.
2. More modern than Angular, gentler learning curve.
3. Composition API provides React-like patterns with better TypeScript integration.
4. Smaller bundle size vs Angular.

**Consequences**:
- **Positive**: Developer satisfaction, faster iteration, excellent TypeScript support.
- **Negative**: Smaller enterprise ecosystem vs Angular; team needs Vue training if coming from Angular background.

**Alternatives Considered**:
- Angular: Better enterprise tooling, RxJS built-in, but heavier and more opinionated.
- React: Largest ecosystem, but license concerns (historical), more boilerplate than Vue.

### ADR-003: Task Queue - Celery vs Azure Functions vs Custom

**Status**: Accepted (2025-11-21)

**Decision**:
Use **Celery + Redis** for worker task queue.

**Rationale**:
1. Mature, battle-tested at scale (>1M tasks/day proven).
2. Rich retry/backoff/timeout configuration.
3. Monitoring via Flower dashboard.
4. Integrates seamlessly with FastAPI.
5. No vendor lock-in (can run anywhere).

**Consequences**:
- **Positive**: Proven reliability, flexible execution modes, easy local development.
- **Negative**: Need to manage Redis cluster; slightly more complex deployment vs Azure Functions.

**Alternatives Considered**:
- Azure Functions: Serverless scaling, but cold starts (3-5s), 10-min timeout limit problematic for long reports.
- Azure Container Apps + KEDA: Good middle ground, but less mature ecosystem than Celery.

### ADR-004: PDF Generation - Puppeteer vs WeasyPrint vs ReportLab

**Status**: Accepted (2025-11-21)

**Decision**:
Use **WeasyPrint** for HTML→PDF conversion.

**Rationale**:
1. Pure Python (no Node.js dependency).
2. CSS Paged Media support (headers, footers, page breaks).
3. Good performance for report-style documents.
4. Fallback: ReportLab for programmatic PDF if template complexity grows.

**Consequences**:
- **Positive**: Simple deployment, no browser emulation overhead.
- **Negative**: Limited JavaScript rendering (but reports are static); complex CSS might need tuning.

**Alternatives Considered**:
- Puppeteer/Playwright: Best HTML/CSS/JS fidelity, but requires Chromium binary (~200MB); Python bindings less mature.
- ReportLab: Fastest, but requires coding layouts vs HTML templates; steeper learning curve for non-devs.
