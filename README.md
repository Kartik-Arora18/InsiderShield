# InsiderShield — Phase 1: Foundation

## Requirements
- Docker Desktop with Docker Compose v2
- VS Code

## Start (Windows PowerShell)
```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api pytest -q
```
Open http://localhost:8000/docs, http://localhost:8000/health/live and http://localhost:8000/health/ready.

Stop: `docker compose down`
Delete local DB data: `docker compose down -v` (destructive).

## Phase 1 includes
FastAPI, PostgreSQL 16, Redis 7, async SQLAlchemy, Alembic migration, organization model, health/readiness endpoints, and smoke tests.

## Next phases
2. Identity, JWT, RBAC and tenant authorization.
3. Event ingestion and durable outbox.
4. Detection rules, risk scoring and alerts.
5. ML anomaly detection and evaluation.
6. Investigations, audit trail and frontend.
7. Integration, E2E tests and demo.

Development-only foundation. Use synthetic or explicitly authorized activity data. Do not deploy publicly without secrets management, TLS, hardened DB roles/RLS, backups, monitoring and security review.
