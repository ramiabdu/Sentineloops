# Backend

FastAPI application layer for SentinelOps.

## Planned responsibilities
- account onboarding APIs
- scan lifecycle APIs (trigger/status summaries implemented)
- findings retrieval APIs (implemented)
- authentication (mock bearer sessions implemented) and RBAC
- risk scoring orchestration (implemented for persisted scanner findings)
- scan execution orchestration (implemented for queued worker scans)
- finding deduplication (implemented with first/last seen and occurrence tracking)
- persistence via repositories
