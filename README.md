# SentinelOOps

SentinelOps is a production-style **Cloud Security Posture Management (CSPM)** MVP designed to detect, prioritize, and manage cloud security misconfigurations across multiple cloud accounts.

This repository is intentionally structured as a **monorepo** so backend, frontend, workers, infrastructure, and documentation evolve together.

## Why this project exists

The goal is to build a serious portfolio grade system that demonstrates:
- clean architecture
- security minded backend design
- scalable scanner/plugin foundations
- observable async workflows
- infrastructure awareness
- strong documentation and developer ownership

The project scope and 30 day roadmap are based on the supplied SentinelOps specification.

## Day 1 outcome

Today's deliverable focuses on the **foundation**:
- monorepo initialized
- clean folder layout
- professional README
- MIT license
- architecture/threat model/decisions docs
- backend skeleton prepared for FastAPI
- frontend and worker placeholders created
- Docker/Terraform/GitHub Actions scaffolding added
- one command local bootstrap path defined

## Planned architecture

```text
sentinelops/
├── backend/            # FastAPI app, domain services, repositories, scanners
├── frontend/           # Dashboard UI
├── workers/            # Async scan/background job workers
├── docker/             # Local development orchestration
├── terraform/          # Infrastructure modules
├── docs/               # Architecture, decisions, roadmap, threat model
├── tests/              # Backend/frontend/integration tests
└── .github/workflows/  # CI pipelines
```

## Tech direction

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy / Alembic
- Pydantic settings
- PostgreSQL
- Redis
- Celery or RQ (planned)

### Frontend
- React + TypeScript + Vite (planned)
- Dashboard oriented component layout

### Infrastructure
- Docker Compose for local development
- Terraform module skeletons for baseline cloud resources
- GitHub Actions for CI

## Repository structure

```text
sentinelops/
├── .github/workflows/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── scanners/
│   │   ├── schemas/
│   │   └── services/
├── docker/
├── docs/
├── frontend/
├── infra/
├── scripts/
├── terraform/
│   └── modules/
├── tests/
└── workers/
```

## Quick start

### 1) Bootstrap environment

```bash
cp .env.example .env
```

### 2) Review docs

Start with:
- `docs/architecture.md`
- `docs/threat model.md`
- `docs/decisions.md`
- `docs/roadmap.md`

### 3) Local development

```bash
make bootstrap
make tree
```

Dockerized local runtime is scaffolded and will be expanded as backend/frontend services become executable.

## MVP scope from specification

The target MVP includes multi account onboarding, a security scanning engine, findings persistence, risk scoring, REST APIs, background workers, dashboard UI, auth/RBAC, alerts, audit logs, CI/CD, local Docker, Terraform, and professional documentation.

Required scanners include:
- public S3 buckets
- open security groups (`0.0.0.0/0`)
- IAM users without MFA
- old access keys
- missing storage encryption

## Development roadmap

The full 30 day plan progresses from repo setup, backend foundations, database/migrations, scanners, persistence, async jobs, frontend dashboard, auth/RBAC, CI, and release polish.

## Definition of done

The repository aims to satisfy the provided definition of done:
- local run path
- usable dashboard
- documented API
- working scanners
- persisted findings
- visible risk score
- passing tests and CI
- professional docs

## Next implementation milestones

1. FastAPI application skeleton + health endpoint
2. configuration management and settings
3. database models for accounts/findings/scans
4. migrations and bootstrap
5. scanner interface + first cloud checks
6. async worker execution model
7. dashboard slices and CI hardening

## License

MIT
## Current endpoints

- `/`
- `/health`

## Runtime behavior

Application logs startup metadata including environment and debug mode.
