# Architectural Decisions

## ADR-001: Monorepo structure
**Decision:** Use a single repository for backend, frontend, workers, infrastructure, docs, and tests.

**Why:** The provided spec explicitly expects this structure, and it improves visibility for a portfolio-grade MVP.

## ADR-002: Python + FastAPI backend
**Decision:** Implement the backend in Python using FastAPI.

**Why:** The specification permits Python FastAPI or Go, and FastAPI offers fast iteration, strong typing with Pydantic, and excellent API ergonomics for MVP velocity.

## ADR-003: Repository pattern + service layer
**Decision:** Keep persistence and business logic separate.

**Why:** This matches the requirement for clean architecture, modular services, validation, and robust error handling.

## ADR-004: Async scanning
**Decision:** Execute cloud scans out-of-band via workers.

**Why:** Scan jobs are I/O-heavy and align naturally with the requirement for async scan jobs and background workers.

## ADR-005: PostgreSQL + Redis
**Decision:** Use PostgreSQL for durable relational state and Redis for queue/cache coordination.

**Why:** This is a pragmatic baseline for findings, scans, accounts, and background job orchestration.

## ADR-006: SQLAlchemy + Alembic as schema source of truth
**Decision:** Use SQLAlchemy ORM models together with Alembic migrations for relational schema evolution.

**Why:** This keeps data models explicit in code while making database changes reproducible, reviewable, and safe to bootstrap across local environments.

## ADR-007: Docker Compose for the full local stack
**Decision:** Run the API, PostgreSQL, and Redis together in Docker Compose for local development.

**Why:** The project now spans application code, schema migrations, and runtime dependencies. A single compose stack reduces local drift and gives future scanner/worker work a stable base.

## ADR-008: Application factory + centralized API router
**Decision:** Structure the FastAPI app around `create_application()`, lifespan hooks, and a central API router that includes route modules.

**Why:** This keeps bootstrap concerns out of handlers, makes testing easier, and gives the codebase a predictable structure before onboarding, findings, and scan endpoints are added.
