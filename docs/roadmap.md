# Roadmap

## 30-day build path

The execution roadmap is derived from the provided 30-day GitHub plan.

### Phase 1 — Foundations
- Day 1: monorepo, README, license
- Day 2: FastAPI backend skeleton + health endpoint
- Day 3: config management and settings
- Day 4: database models
- Day 5: Alembic and DB bootstrap
- Day 6: Docker Compose stack
- Day 7: refactor and architecture docs

### Phase 2 — Core product behavior
- account onboarding API
- validation + error handling
- scanner interface
- concrete cloud scanners, including S3 public buckets, security group exposure, and IAM users without MFA
- persistence of findings
- risk scoring engine
- findings APIs
- scan trigger/status tracking
- async worker execution model
- deduplication with first/last seen tracking

### Phase 3 — Execution and UI
- frontend dashboard skeleton
- accounts page
- findings table
- severity charts
- finding details

### Phase 4 — Hardening and release
- authentication
- RBAC
- CI/tests/lint
- docs and release polish
