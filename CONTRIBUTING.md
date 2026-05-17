# Contributing

Thanks for considering a contribution to SentinelOps.

## Development Setup

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make up
```

## Quality Checks

Backend:

```bash
cd backend
python -m pytest ../tests/backend
python -m ruff check app ../tests/backend
```

Frontend:

```bash
cd frontend
npm run test
npm run build
```

## Pull Request Guidelines

- Keep changes focused.
- Include tests for backend behavior changes.
- Update docs when behavior, setup, or deployment changes.
- Do not commit secrets or local environment files.
- Explain the user/security impact in the PR description.

## Commit Style

Use clear conventional-style subjects when possible:

```text
feat(api): add scanner status endpoint
fix(worker): handle failed scan transitions
docs: clarify Railway deployment steps
```
