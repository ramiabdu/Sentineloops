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

## Backend layers

### API layer
Handles:
- request validation
- authentication/authorization
- pagination/filtering
- response models
- error mapping

### Service layer
Implements business use cases:
- onboarding accounts
- starting scans
- calculating risk
- listing and triaging findings

### Repository layer
Abstracts persistence:
- accounts repository
- findings repository
- scans repository
- audit log repository

### Scanner layer
Plugin-oriented interfaces isolate cloud checks:
- S3 exposure scanner
- security group exposure scanner
- IAM MFA scanner
- access key age scanner
- storage encryption scanner

## Data model direction

Core entities:
- `accounts`
- `scans`
- `findings`
- `audit_logs`
- `users`
- `roles`

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

Local development will use Docker Compose. Cloud deployment will evolve via Terraform modules for networking baseline, app skeleton, storage, and IAM examples as required by the spec.
