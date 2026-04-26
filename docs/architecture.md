# Architecture

## Overview

SentinelOps follows a modular monorepo structure aligned with the project specification for backend, frontend, workers, infrastructure, Docker, Terraform, tests, and docs.

## System context

```text
Cloud Accounts ──> Scanner Engine ──> Findings Pipeline ──> Database
        │                 │                  │                 │
        │                 │                  └──> Risk Scoring │
        │                 └──> Async Jobs                      │
        └──────────────────────────────────────────────────────┘
                                   │
                                   v
                              REST API ──> Dashboard UI
```

## Current backend package layout

```text
backend/app/
├── api/
│   ├── router.py
│   └── routes/
│       └── health.py
├── core/
│   ├── config.py
│   ├── lifecycle.py
│   └── logging.py
├── db/
│   └── session.py
├── models/
│   ├── account.py
│   ├── base.py
│   ├── finding.py
│   └── scan.py
└── schemas/
    └── health.py
```

## Backend layers

### API layer
Current role:
- central route aggregation via `api/router.py`
- route modules under `api/routes/`
- response contracts in `schemas/`

Planned growth:
- request validation
- authentication/authorization
- pagination/filtering
- error mapping

### Service layer
Business use cases will live here:
- onboarding accounts
- starting scans
- calculating risk
- listing and triaging findings

### Repository layer
Persistence boundaries will live here:
- accounts repository
- findings repository
- scans repository
- audit log repository

### Scanner layer
Plugin-oriented cloud checks will live here:
- S3 exposure scanner
- security group exposure scanner
- IAM MFA scanner
- access key age scanner
- storage encryption scanner

## Data model status

Implemented:
- `accounts`
- `scans`
- `findings`

Planned:
- `audit_logs`
- `users`
- `roles`

## Request/runtime flow

1. `create_application()` builds the FastAPI app.
2. `core/lifecycle.py` handles startup logging through lifespan.
3. `api/router.py` aggregates route modules.
4. Route handlers return typed schema responses.
5. `db/session.py` owns engine/session creation for future repository usage.
6. Alembic migrations bootstrap the schema before API startup in Docker.

## Async execution direction

The specification requires async scan jobs and background workers. Planned flow: API creates a scan request, worker executes scanner plugins, findings are normalized, deduplicated, risk-scored, then persisted.

## Security posture principles

- least privilege by default
- secure configuration defaults
- secrets never committed
- JWT or equivalent auth
- auditable state-changing actions
- rate limiting at API boundary

## Deployment direction

Current local development uses Docker Compose with:
- FastAPI API container
- PostgreSQL 16
- Redis 7
- Alembic migration bootstrap on API startup

Cloud deployment will evolve via Terraform modules for networking baseline, app skeleton, storage, and IAM examples as required by the spec.
