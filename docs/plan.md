# Project Plan

## 1. Overview
Defines phases, milestones, roles, risks, and success metrics for delivery of the Report Scheduler platform.

**Technology Stack**: Python 3.11+ (FastAPI, Celery) + Vue 3 (TypeScript, Composition API) + Azure infrastructure. See ADR-001 in design.md for rationale.

## 2. Objectives
- Reliable scheduling & delivery of analytical reports.
- Multi-channel distribution (email, Slack, webhook) with audit trails.
- Scalable architecture supporting growth from tens to thousands of schedules.
- Secure multi-tenant isolation.

## 3. Scope (MVP)
- CRUD for reports & schedules.
- CSV + PDF output.
- Email delivery.
- Run status dashboard + artifact download.
- Authentication & RBAC.

## 4. Out-of-Scope (MVP)
- Slack/webhook delivery.
- Advanced templating components.
- Real-time event-triggered reports.
- ML summarization.

## 5. Phases & Milestones
### Phase 1: Discovery & Design (Weeks 1-2)
Architecture, domain modeling, ADRs, backlog.
Milestone: Approved architecture & backlog.
### Phase 2: Core Backend & Data Layer (Weeks 3-6)
Report & schedule APIs, schema, scheduler baseline, event bus.
Milestone: Schedules create queued executions.
### Phase 3: Generation & Artifact Pipeline (Weeks 7-9)
Worker pipeline, PDF/CSV, storage integration.
Milestone: End-to-end generation.
### Phase 4: Delivery & Notifications (Weeks 10-11)
Email service, audit logging.
Milestone: Delivered report email.
### Phase 5: Frontend & UX (Weeks 10-12 overlap)
UI for definitions, schedules, runs, artifacts.
Milestone: Usable MVP UI.
### Phase 6: Testing & Hardening (Weeks 13-14)
Automated tests, performance baseline, security review.
Milestone: Readiness report.
### Phase 7: Deployment & Launch (Weeks 15-16)
IaC, CI/CD finalization, monitoring dashboards, go-live.
Milestone: Production launch.
### Phase 8: Iteration (Post-launch)
Enhancements (Slack/webhook, advanced templates), optimization.

## 6. Timeline Summary
Indicative MVP duration ~16 weeks; revisit monthly.

## 7. Roles
- Product Owner: requirements & prioritization.
- Tech Lead: architecture & quality gates.
- Backend Engineers (2): APIs, scheduler, workers, delivery.
- Frontend Engineer (1): UI/UX.
- DevOps (0.5): IaC, CI/CD, observability.
- QA (0.5): test automation & performance.
- Security Advisor (as-needed): threat modeling & review.

## 8. Resource Estimates
Velocity assumptions: ~20 story points / sprint (2 weeks) across team; adjust after sprint 2.

## 9. Deliverables Per Phase
Design docs, schemas, services, workers, storage integration, UI components, tests, runbook, monitoring dashboards.

## 10. Dependencies
Email provider, object storage bucket, analytics data source access, secret management, queue infrastructure.

## 11. Risk Management
| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| Query performance | Slow reports | Timeouts + pre-aggregation | Backend |
| Schedule duplication | Extra runs | Distributed lock + idempotency | Tech Lead |
| Email deliverability | Poor UX | SPF/DKIM set early | DevOps |
| Scope creep | Delay | Strict MVP boundary + backlog triage | Product |
| Security gaps | Compliance risk | Early scans + review | Security |

## 12. Communication Plan
Daily stand-up; weekly sprint review; architecture sync bi-weekly; dashboard updates twice weekly.

## 13. Quality Gates

**Code Quality**:
- Linting: Ruff (Python), ESLint (Vue), no errors allowed.
- Type coverage: mypy strict mode (Python), TypeScript strict (Vue).
- Code coverage: >80% overall, >90% for business logic (service layer).
- Security scan: Snyk/Bandit (Python), npm audit (Vue), no high/critical vulnerabilities.
- Complexity: Max cyclomatic complexity 10 per function.

**Testing Requirements**:
- **Unit Tests**: pytest (Python), vitest (Vue). Fast (<1s per test), isolated (mocked dependencies).
  - Coverage target: 85% line coverage.
  - Required: All service layer, domain models, composables.
- **Integration Tests**: Test with real PostgreSQL (Docker), Redis, mocked Service Bus.
  - Coverage: Repository layer, API endpoints (happy + error paths).
  - Performance: <5s per test suite.
- **Contract Tests**: Pact for API consumer/provider contracts (frontend ↔ backend).
  - Verify request/response schemas don't break between versions.
- **E2E Tests**: Playwright (Vue) for critical user flows.
  - Scenarios: Create report → schedule with email → verify gallery shows artifact → download PDF.
  - Run in Staging before prod deploy.
- **Performance Tests**: Locust (Python) load testing.
  - Baseline: 100 concurrent users, p95 response time <500ms.
  - Smoke test in CI; full load test weekly in perf environment.
- **Security Tests**: OWASP ZAP automated scan, manual penetration test before GA.

**Deployment Gates**:
- All tests passing (unit, integration, contract).
- Security scan clean (no high/critical).
- Performance regression: p95 latency not >10% vs baseline.
- Manual review approval for production deploys.

## 14. Success Criteria
- Trigger adherence >95%.
- Failed executions <2% (excl. data issues).
- Median generation <30s.
- First pilot tenants satisfied (qualitative feedback).
- Zero P1 security incidents first quarter.

## 15. Post-Launch KPIs
Active schedules, delivery success rate, p95 generation time, support tickets per tenant, infra cost per execution.

## 16. Change Management
ADRs for major design shifts; monthly backlog re-baseline using KPIs.

## 17. Exit Criteria MVP
All success criteria met + validated runbook + on-call simulation pass.

---
Living document; updates via PR referencing rationale & metrics.
