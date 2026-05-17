# Backend

FastAPI application layer for SentinelOps.

## Responsibilities

- Account onboarding APIs
- Scan trigger, lifecycle, and status APIs
- Findings retrieval APIs with filters
- Mock bearer authentication and RBAC route checks
- Risk scoring for persisted scanner findings
- Queued scan execution orchestration
- Finding deduplication with first/last seen and occurrence tracking
- SQLAlchemy repositories and Alembic migrations

## Local checks

```bash
python -m pytest ../tests/backend
python -m ruff check app ../tests/backend
```
