# Threat Model

## Objective

Identify the main security risks to SentinelOps as a cloud security platform.

## Assets

- cloud account metadata
- findings and risk scores
- access credentials and tokens
- audit logs
- user sessions / JWTs
- scanner execution results

## Trust boundaries

1. Browser ↔ API
2. API ↔ Database
3. API ↔ Redis / Queue
4. Worker ↔ Cloud Provider APIs
5. CI/CD ↔ Container/Artifact registry

## Primary threats

### Secrets exposure
Risk: leaked cloud credentials, JWT secrets, webhook tokens.
Mitigation:
- `.env` excluded from git
- secret manager strategy documented
- least privilege cloud roles
- no hardcoded credentials

### Broken access control
Risk: one tenant/operator viewing or modifying unauthorized data.
Mitigation:
- JWT auth
- RBAC
- explicit authorization checks in service layer
- audit logging for sensitive actions

### Scanner abuse
Risk: untrusted scanner input or plugin misuse causing data leakage or remote execution.
Mitigation:
- controlled scanner registry
- typed scanner contracts
- timeouts and execution isolation
- normalized outputs

### Injection vulnerabilities
Risk: SQL injection or command injection through onboarding or scan parameters.
Mitigation:
- ORM/repository patterns
- strict schema validation
- avoid shell execution from user input

### Findings tampering
Risk: manipulated risk scores or scan history.
Mitigation:
- immutable-ish audit log entries
- server-side scoring only
- state transitions validated in service layer

### Supply chain risk
Risk: compromised dependencies or CI.
Mitigation:
- pinned dependencies where practical
- CI lint/test/build gates
- minimal permissions in GitHub Actions

## Secure defaults checklist

- deny-by-default authorization model
- strong secret key requirements
- production config separation
- explicit CORS configuration
- structured logs with sensitive field redaction
