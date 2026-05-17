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
│       ├── findings.py
│       ├── health.py
│       └── scans.py
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
│   ├── risk.py
│   ├── scan_execution.py
│   └── scans.py
└── schemas/
    ├── account.py
    ├── errors.py
    ├── finding.py
    ├── health.py
    └── scan.py
```

## Current frontend shape

The Vite React frontend now starts on a responsive dashboard skeleton with:
- posture metric cards
- account navigation and onboarding form
- priority findings preview
- filterable findings table
- finding details panel
- severity charts and risk cards
- cloud account inventory
- scan activity tracking

## Backend layers

### API layer
Current role:
- central route aggregation via `api/router.py`
- route modules under `api/routes/`
- request validation through Pydantic schemas
- mock bearer session authentication via `/auth/session` and `/auth/me`
- role checks for read-only viewers, scan-triggering analysts, and account-managing admins
- findings list/detail APIs with account, scan, severity, status, and scanner filters
- scan trigger/status APIs for queueing and inspecting scan jobs with finding counts
- standardized JSON error responses
- response contracts in `schemas/`

Planned growth:
- persistent users and role assignments
- pagination/filtering

### Service layer
Business use cases will live here:
- onboarding accounts
- persisting scanner findings
- deduplicating repeated scanner observations with first/last seen tracking
- calculating deterministic finding risk scores from severity and scanner context
- starting scans as queued jobs
- executing queued scans and updating scan lifecycle state
- summarizing scan progress with duration and finding counts
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
8. `services/findings.py` deduplicates and persists scanner output as account- and scan-linked findings.
9. `services/scan_execution.py` moves queued scans through running, completed, or failed states.
10. `workers/app/main.py` polls for queued scans and delegates execution to backend services.
11. `services/scans.py` builds scan status snapshots with lifecycle timing and finding counts.
12. `db/session.py` owns engine/session creation for repository usage.
13. `core/auth.py` validates mock bearer session tokens and route role requirements.
14. Alembic migrations bootstrap the schema before API startup in Docker.

## Async execution direction

The worker execution model now supports a polling loop that claims queued scans, executes scanner plugins, deduplicates and persists findings, and records completion or failure state. Redis remains available in the local stack for a future queue-backed implementation.

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
- scan worker container
- PostgreSQL 16
- Redis 7
- Alembic migration bootstrap on API startup

GitHub Actions now validates backend lint/tests and frontend typecheck/build before changes land on `main`.

Cloud deployment will evolve via Terraform modules for networking baseline, app skeleton, storage, and IAM examples as required by the spec.
