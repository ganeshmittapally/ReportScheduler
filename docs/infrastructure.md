# Infrastructure

## 1. Overview
Defines Azure-based cloud architecture, Terraform IaC, environments, CI/CD, observability, resilience, and cost strategies for the Report Scheduler platform.

**Technology Stack**: Python 3.11+ backend (FastAPI APIs + Celery workers) deployed on Azure Container Apps with KEDA autoscaling. Vue 3 frontend (Vite build) served via Azure Static Web Apps or CDN.

## 2. Principles
- Immutable infrastructure via Terraform IaC.
- Secure by default (least privilege, encrypted storage, audited changes).
- Observability baked into each component.
- Horizontal scale preference; small stateless units.
- Multi-tenant isolation enforced at data + network layers.

## 3. Environments
| Env | Purpose | Data | Scaling | Access |
|-----|---------|------|---------|--------|
| LOCAL | Developer laptop | Docker Compose | Single instance | Individual dev |
| DEV | Developer integration | Synthetic | Minimal (B1) | Engineers |
| STAGE | Pre-prod verification | Masked subset | Mirrors prod (scaled down) | Engineers + QA |
| PROD | Live workloads | Real | Autoscaled | Limited ops |
| PERF (optional) | Load / stress tests | Synthetic large | On-demand | Engineers |

## 3a. Local Development Setup

**Prerequisites**:
- Docker Desktop, Python 3.11+, Node.js 20+, Azure CLI, Terraform.

**Quick Start** (from project root):
```bash
# Start dependencies via Docker Compose
docker-compose up -d postgres redis

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head  # Run migrations
uvicorn src.main:app --reload --port 8000

# Frontend setup (separate terminal)
cd frontend
npm install
npm run dev  # Starts Vite dev server on port 5173

# Worker (separate terminal)
cd backend
celery -A src.workers.celery_app worker --loglevel=info

# Scheduler (separate terminal)
cd backend
python -m src.scheduler.scheduler_loop
```

**Docker Compose** (`docker-compose.yml` in root):
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: reportscheduler
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Optional: localstack for Azure emulation
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite
    ports:
      - "10000:10000"  # Blob
    command: azurite-blob --blobHost 0.0.0.0

volumes:
  postgres_data:
```

**Environment Variables** (`.env.local`):
```
DATABASE_URL=postgresql://dev:devpass@localhost:5432/reportscheduler
REDIS_URL=redis://localhost:6379/0
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
JWT_SECRET=dev-secret-change-in-prod
ENVIRONMENT=local
```

## 4. Azure Resources (Terraform-managed)
### Networking
- Virtual Network (VNet) with subnets: `frontend-subnet`, `backend-subnet`, `data-subnet`.
- Network Security Groups (NSGs) per subnet with deny-by-default rules.
- Application Gateway (WAF-enabled) for ingress.
- Private Endpoints for Azure services (Storage, Key Vault, PostgreSQL).

### Compute
- Azure Container Instances (ACI) or Azure Kubernetes Service (AKS) for services.
  - API Service (Container Apps or AKS deployment).
  - Scheduler Service (separate deployment).
  - Worker Pool (autoscaled based on queue depth).
- Option: Azure Container Apps for serverless scaling with KEDA.

### Messaging & Eventing
- Azure Service Bus (Premium tier) with topics/subscriptions for execution events.
- Dead-letter queue for failed message processing.
- Alternative: Azure Event Hubs for high-throughput scenarios.

### Data Layer
- Azure Database for PostgreSQL (Flexible Server) with:
  - Zone-redundant HA in PROD.
  - Read replicas for analytical queries.
  - Automated backups (7-35 day retention).
- Azure Cache for Redis (Standard/Premium) for locks & caching.

### Storage
- Azure Blob Storage (Hot tier) for artifacts:
  - Container per tenant or shared with path prefix isolation.
  - Lifecycle management policies (transition to Cool after 30d, delete after 90d).
  - Versioning + soft delete enabled.
  - Server-side encryption with customer-managed keys (CMK) in Key Vault.

### Security & Secrets
- Azure Key Vault for secrets, certificates, encryption keys.
- Managed Identities for service authentication (no stored credentials).
- Azure AD integration for user authentication (OAuth2/OIDC).

### Observability
- Azure Monitor + Application Insights for metrics, logs, traces.
- Log Analytics workspace for centralized logging.
- Azure Workbooks for custom dashboards.
- OpenTelemetry instrumentation sending to Application Insights.

## 5. Networking & Security
- Frontend subnet: public-facing Application Gateway only.
- Backend subnet: private services with NSG rules allowing only required ports.
- Data subnet: isolated PostgreSQL & Redis; no internet egress.
- Private Endpoints prevent data exfiltration via public IPs.
- WAF at Application Gateway: OWASP Top 10 rule sets enabled.
- Azure DDoS Protection Standard (for PROD).
- TLS 1.2+ enforced; certificates via Azure Key Vault or managed certs.

## 6. Identity & Access Management
- Managed Identities per service (System-assigned or User-assigned).
- RBAC assignments via Terraform:
  - API Service: `Key Vault Secrets User`, `Storage Blob Data Contributor`.
  - Workers: `Storage Blob Data Contributor`, `Service Bus Data Receiver`.
- Break-glass admin with Privileged Identity Management (PIM).
- Conditional Access policies for engineering team.

## 7. Infrastructure as Code (Terraform)
### Structure
```
infra/
  modules/
    network/
    compute/
    database/
    storage/
    messaging/
    monitoring/
  environments/
    dev/
    stage/
    prod/
  terraform.tfvars (per env)
  backend.tf (Azure Storage backend)
```

### Best Practices
- Remote state in Azure Storage with state locking via blob lease.
- Terraform Cloud or Azure DevOps for plan/apply automation.
- Module versioning via Git tags; pin module versions in env configs.
- Terraform plan output attached to PR for review.
- Tag all resources: `environment`, `owner`, `cost_center`, `project`.

### Example Resources
- `azurerm_virtual_network`
- `azurerm_postgresql_flexible_server`
- `azurerm_container_app` or `azurerm_kubernetes_cluster`
- `azurerm_servicebus_namespace`
- `azurerm_storage_account` + `azurerm_storage_container`
- `azurerm_key_vault`
- `azurerm_log_analytics_workspace`

## 8. CI/CD Pipeline (Azure DevOps or GitHub Actions)
### Stages
1. **Source** → Checkout, dependency caching.
2. **Static Analysis** → ESLint/Ruff, TypeScript/Python type check, secret scan (GitGuardian/Gitleaks).
3. **Unit Tests** → Parallel execution with coverage reports.
4. **Integration Tests** → Ephemeral PostgreSQL + Redis containers.
5. **Security Scan** → Trivy/Snyk for container images + dependencies.
6. **Build Artifact** → Docker image pushed to Azure Container Registry (ACR) tagged with git SHA + semver.
7. **Terraform Plan** (non-prod) → Automated plan, manual review.
8. **Deploy DEV** → Terraform apply, smoke tests.
9. **Deploy STAGE** → Terraform apply, automated E2E tests.
10. **Manual Gate** → Approval for PROD.
11. **Deploy PROD** → Canary (10% traffic) → metrics evaluation → full rollout.

### Rollback
- Revert to previous image tag in ACR.
- Terraform state snapshot; rollback plan pre-tested.

## 9. Observability Stack
### Metrics
- Application Insights custom metrics: `schedule_trigger_lag_seconds`, `report_generation_duration`, `delivery_latency_p95`.
- Azure Monitor for infrastructure: CPU, memory, disk, network.
- Service Bus metrics: message count, dead-letter count.

### Logs
- Structured JSON logs sent to Application Insights.
- Log retention: 90 days in Log Analytics (configurable).
- Query via Kusto Query Language (KQL).

### Traces
- OpenTelemetry SDK in services → Application Insights.
- Distributed tracing across API → Scheduler → Worker → Delivery.

### Dashboards
- Azure Workbooks:
  - Scheduler lag trends.
  - Queue depth & processing rate.
  - Success vs failure ratio per tenant.
  - Artifact size distribution.

### Alerts
- Action Groups for PagerDuty/email/Slack.
- Alert rules:
  - Queue depth > 1000 messages for 10 min.
  - Execution failure rate > 5% in 15 min.
  - Database CPU > 80% for 5 min.
  - Generation duration p95 > 60s.

## 10. Resilience & HA
- PostgreSQL zone-redundant HA (automatic failover).
- Redis Premium with clustering + zone redundancy.
- Container Apps or AKS with multi-zone node pools.
- Service Bus geo-replication (optional for DR).
- Graceful shutdown: preStop hooks drain active work.
- Health probes (liveness, readiness) for auto-restart.

## 11. Backup & Disaster Recovery
### Database
- Automated backups: daily full, 5-min incremental.
- Retention: 7 days (DEV/STAGE), 35 days (PROD).
- Point-in-time restore (PITR) capability.

### Blob Storage
- Soft delete: 14 days (PROD).
- Versioning enabled for critical containers.
- Geo-redundant storage (GRS) for PROD artifacts (optional).

### Redis
- Persistence enabled (RDB snapshots) for Premium tier.
- No backup for cache-only data.

### DR Targets
- RPO: < 15 min (via incremental backups).
- RTO: < 2 hours (restore + validation).

### DR Procedures (Detailed)

**Scenario 1: Database Failure (Primary Region)**
1. Automated: Azure PostgreSQL auto-failover to zone-redundant standby (<1 min).
2. If zone-level failure: Manual failover to read replica in secondary region.
3. Steps: Promote read replica to primary via Azure CLI; update connection strings in Key Vault; restart API/worker services.
4. Validation: Run smoke tests (create schedule, trigger execution, verify artifact upload).

**Scenario 2: Complete Regional Outage**
1. Trigger: Azure Health Service reports region unavailable >15 min.
2. Activate DR site (secondary region with standby infrastructure via Terraform).
3. Steps:
   - Update Traffic Manager to route to DR region.
   - Promote PostgreSQL read replica.
   - Start Container Apps in DR region (pre-warmed images).
   - Verify Service Bus failover (geo-replication).
   - Update DNS (if not using Traffic Manager).
4. Data consistency: Check replication lag (<5 min acceptable); identify any in-flight executions and re-queue.
5. Validation: Full E2E test suite in DR region.
6. Communication: Status page update; email to tenant admins.

**Scenario 3: Data Corruption / Accidental Deletion**
1. Restore from point-in-time backup (PostgreSQL PITR).
2. For specific tables: Export from backup; merge into prod with deduplication.
3. For Blob Storage: Restore from soft-delete or version history.

### Runbook
- Incident classification: P1 (service down), P2 (degraded), P3 (isolated issue), P4 (cosmetic).
- Escalation: P1 → immediate on-call page; P2 → alert within 30 min; P3/P4 → ticket queue.
- Failover steps: Documented in wiki with screenshots; tested quarterly.
- Post-incident: RCA within 48h; action items tracked in backlog.

## 12. Performance & Scaling
### Autoscaling
- Container Apps: scale on HTTP queue depth + CPU.
- Workers: scale on Service Bus queue depth (KEDA scaler).
- Target: queue processing latency < 10s.

### Database
- Read replicas for analytics; writes to primary only.
- Connection pooling via PgBouncer (sidecar or separate ACI).
- Query performance insights enabled.

### Caching Strategy
- Redis:
  - Schedule next-fire times (TTL = time to next evaluation).
  - Report definitions (invalidate on update).
  - Recent run statuses (TTL = 5 min).
- HTTP response caching: minimal due to tenant-specific data.

### Rate Limiting
- Application Gateway rate limiting per tenant (custom rules).
- API-level throttling: 100 req/min per tenant (configurable).

## 13. Cost Optimization
### Compute
- Use Azure Container Apps (serverless) for bursty workloads.
- Scale workers to zero during idle periods.
- Reserved instances for baseline load (PROD).

### Storage
- Lifecycle policies: Hot → Cool (30d) → Archive (90d, if regulatory).
- Delete ephemeral artifacts after retention period.
- Compress large CSV/JSON (gzip) before upload.

### Database
- Rightsize after performance baselining (start B2ms, scale as needed).
- Use Burstable tier for DEV/STAGE.
- Archive old audit logs to Blob Storage.

### Monitoring
- Log sampling for high-volume INFO logs in PROD.
- Alert only on actionable metrics; avoid noise.

### Cost Dashboard
- Azure Cost Management + Budgets with alerts at 80% threshold.
- Tag-based cost allocation per environment/team.

## 14. Compliance & Audit
- Azure Policy enforcement: require tags, encryption, NSGs.
- Activity logs exported to Log Analytics for audit trail.
- Immutable audit events table (append-only).
- Data residency: select Azure region per compliance (EU, US, Asia).

## 15. Secrets Management
- All secrets in Key Vault; rotation policies (30-90 days).
- Managed Identities for service-to-service auth (no passwords).
- CI secrets via Azure DevOps secure variables or GitHub encrypted secrets.

## 16. Deployment Strategy
- **Canary**: 10% traffic via Application Gateway weighted routing.
- **Metrics evaluation**: error rate, p95 latency over 15 min.
- **Rollback trigger**: automated if error threshold breached.
- **Blue-Green**: for major DB schema migrations (parallel envs).

## 17. Logging Standards
- Mandatory fields: `timestamp`, `level`, `service`, `tenantId`, `traceId`, `runId`.
- No PII in logs; hash identifiers if necessary.
- Structured JSON format for KQL queries.

## 18. Runbook & On-Call
### Incident Response
- P1 (service down): escalate immediately, enable DR if needed.
- P2 (degraded): investigate, apply hotfix within 4h.
- Common scenarios: queue backlog, DB connection exhaustion, storage quota.

### Operational Procedures
- Weekly alert review; tune thresholds.
- Monthly cost review & optimization.
- Quarterly DR drill (restore from backup).

## 19. Terraform Workflow
```bash
# Initialize
cd infra/environments/dev
terraform init

# Plan
terraform plan -out=tfplan

# Apply (after PR approval)
terraform apply tfplan

# Destroy (dev/stage only)
terraform destroy
```

## 20. Azure-Specific Optimizations
- Use Azure Front Door for global traffic distribution (future multi-region).
- Azure CDN for static UI assets.
- Proximity Placement Groups for latency-sensitive components.

## 21. Cost Estimation (Initial MVP - 1000 Tenants)

**Monthly Estimates (USD, Azure East US)**:

| Resource | Spec | Monthly Cost |
|----------|------|-------------|
| PostgreSQL Flexible Server | GP_Gen5_8 (8 vCores, 32GB) | $730 |
| Read Replica | GP_Gen5_4 (4 vCores, 16GB) | $365 |
| Redis Premium | P2 (6GB, clustering) | $225 |
| Service Bus Premium | 1 messaging unit | $670 |
| Container Apps | 300 max instances avg 50 (1vCPU, 2GB each) | $400 |
| Blob Storage | 5TB Hot + 10TB Cool + 1M ops | $250 |
| Application Insights | 50GB ingestion | $115 |
| Traffic Manager | 1 Azure endpoint, 10M queries | $50 |
| Key Vault | 10K operations/month | $3 |
| Data Transfer | 1TB egress | $80 |
| **Total** | | **~$2,900/month** |

**Cost Per Tenant**: $2.90/month (at 1000 tenants).
**Break-even**: Pricing >$5/tenant/month achieves profitability.

**Optimization Opportunities**:
- Use Spot/Burstable VMs for non-prod environments (-70%).
- Lifecycle policies on Blob Storage (Cool tier after 30d, -50% storage cost).
- Reserved instances for baseline load (PostgreSQL, -40% for 1-year commit).
- Compress artifacts before upload (reduce storage by ~60% for CSVs).

## 22. Future Enhancements
- Multi-region active-active with Traffic Manager.
- Azure Functions for lightweight event-driven tasks.
- Confidential computing (VMs) for sensitive data processing.
- Azure Front Door + CDN for global UI distribution.

---
Infrastructure definitions evolve; changes documented via Terraform module versioning & ADRs.
