# SentinelOps v1.0.0

## Release Summary

SentinelOps v1.0.0 is the completed 30-day CSPM MVP baseline. It includes a FastAPI backend, scanner plugin architecture, persistence layer, queued scan execution model, responsive React dashboard, authentication/RBAC foundation, CI, documentation, screenshots, and a demo GIF.

## Product Scope

- Cloud account onboarding APIs and dashboard form
- Findings persistence with deduplication, first/last seen tracking, and occurrence counts
- Risk scoring for scanner findings
- Findings list/detail APIs with filters
- Scan trigger and scan status APIs
- Worker polling loop for queued scans
- Mock bearer sessions and RBAC for viewer, analyst, and admin flows
- Responsive dashboard with posture metrics, findings table, severity charts, risk cards, and finding details
- GitHub Actions CI for backend tests/lint and frontend typecheck/build

## Implemented Scanners

- Public S3 bucket exposure
- Public security group ingress
- IAM console users without MFA

## Demo Assets

- Demo GIF: `docs/assets/sentinelops-demo.gif`
- Desktop overview: `docs/assets/sentinelops-overview.png`
- Findings workflow: `docs/assets/sentinelops-findings.png`
- Mobile dashboard: `docs/assets/sentinelops-mobile.png`

## Verification

Validated locally before release:

- `pytest tests/backend`
- `ruff check backend tests/backend`
- `tsc --noEmit`
- `vite build`
- GitHub Actions workflow YAML parse check
- Playwright screenshot capture for desktop, findings, and mobile dashboard states

## Release Tag

This release is tagged as `v1.0.0`.
