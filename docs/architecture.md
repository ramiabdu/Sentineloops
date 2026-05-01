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
│       ├── accounts.py
│       └── health.py
├── core/
│   ├── config.py
│   ├── errors.py
│   ├── exception_handlers.py
│   ├── lifecycle.py
│   └── logging.py
├── db/
│   └── session.py
├── models/
│   ├── account.py
│   ├── base.py
│   ├── finding.py
│   └── scan.py
├── scanners/
│   ├── contracts.py
│   ├── registry.py
│   └── runner.py
├── services/
│   ├── accounts.py
│   ├── findings.py
│   └── risk.py
└── schemas/
    ├── account.py
    ├── errors.py
    └── health.py
```

## Backend layers

### API layer
Current role:
- central route aggregation via `api/router.py`
- route modules under `api/routes/`
- request validation through Pydantic schemas
- standardized JSON error responses
- response contracts in `schemas/`

Planned growth:
- authentication/authorization
- pagination/filtering

### Service layer
Business use cases will live here:
- onboarding accounts
- persisting scanner findings
- calculating deterministic finding risk scores from severity and scanner context
- starting scans
- listing and triaging findings

### Repository layer
Persistence boundaries will live here:
- accounts repository
- findings repository
- scans repository
- audit log repository

### Scanner layer
Implemented role:
- typed scanner contracts for scan targets and finding drafts
- registry for provider-scoped scanner plugins
- runner for default provider scans or explicit scanner selection
- AWS S3 public bucket scanner using a client protocol
- AWS security group open-port scanner using a client protocol
- AWS IAM user without MFA scanner using a client protocol

Concrete cloud checks will live here:
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
5. `core/exception_handlers.py` maps domain and validation errors into stable JSON payloads.
6. Scanner plugins return normalized `FindingDraft` objects.
7. `services/risk.py` assigns normalized 0.00-10.00 risk scores when scanner drafts do not provide one.
8. `services/findings.py` persists scanner output as account- and scan-linked findings.
9. `db/session.py` owns engine/session creation for repository usage.
10. Alembic migrations bootstrap the schema before API startup in Docker.

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
