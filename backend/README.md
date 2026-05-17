# Backend

FastAPI application layer for SentinelOps.

## Responsibilities

- Account onboarding APIs
- Scan trigger, lifecycle, and status APIs
- Findings retrieval APIs with filters
- Public signup, password login, JWT bearer authentication, and RBAC route checks
- Risk scoring for persisted scanner findings
- Queued scan execution orchestration
- Finding deduplication with first/last seen and occurrence tracking
- SQLAlchemy repositories and Alembic migrations

## Local checks

```bash
python -m pytest ../tests/backend
python -m ruff check app ../tests/backend
```

## Swagger auth flow

1. Open `/docs`.
2. Call `POST /auth/signup` with an email, display name, password, and role.
3. Call `POST /auth/login` with the same email and password.
4. Copy the returned `access_token` into Swagger's **Authorize** dialog as a bearer token.
5. Call protected endpoints such as `GET /auth/me` or `GET /accounts`.
