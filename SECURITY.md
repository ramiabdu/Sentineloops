# Security Policy

## Supported Versions

Security fixes are handled on `main` until a formal release support policy is introduced.

## Reporting A Vulnerability

Do not open a public issue for sensitive security reports.

For now, contact the repository owner directly through GitHub. Include:

- affected area
- reproduction steps
- expected impact
- suggested fix, if known

## Security Expectations

- Do not commit secrets, cloud credentials, tokens, or production `.env` files.
- Use least-privilege credentials for scanner integrations.
- Keep `DEBUG=false` outside local development.
- Rotate `AUTH_SECRET_KEY` for every deployed environment.
- Restrict `CORS_ALLOWED_ORIGINS` to trusted frontend domains.

## Current Auth Scope

SentinelOps currently uses public signup, password login, JWT bearer sessions, and route-level RBAC for the MVP. Production identity should be replaced with a real identity provider before handling sensitive customer data.
