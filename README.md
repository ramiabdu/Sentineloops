# SentinelOps

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

## Current foundation state

Days 1-7 currently establish the platform baseline:
- monorepo initialized and documented
- FastAPI application factory and routed API structure
- SQLAlchemy models for accounts, scans, and findings
- Alembic bootstrap and initial schema migration
- local Docker Compose stack for API, PostgreSQL, and Redis
- frontend dashboard skeleton created
- architecture and decision docs updated to match the codebase

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
- React + TypeScript + Vite
- Dashboard oriented component layout

### Infrastructure
- Docker Compose for local development
- Terraform modules for baseline cloud resources
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
cp backend/.env.example backend/.env
```

### 2) Review docs

Start with:
- `docs/architecture.md`
- `docs/threat-model.md`
- `docs/decisions.md`
- `docs/roadmap.md`

### 3) Local development

```bash
make bootstrap
make tree
make up
```

Dockerized local runtime starts the backend API with PostgreSQL and Redis.

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

1. account onboarding API
2. validation schemas and error handling
3. scanner interface and first cloud checks
4. findings persistence flow
5. risk scoring and findings APIs
6. async worker execution model
7. CI hardening and dashboard expansion

## License

MIT
## Current endpoints

- `/`
- `/health`
- `GET /accounts`
- `POST /accounts`
- `GET /accounts/{account_id}`

## Runtime behavior

Application logs startup metadata including environment and debug mode.
