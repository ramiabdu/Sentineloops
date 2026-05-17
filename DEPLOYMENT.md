# SentinelOps Deployment Guide

## Current Deployment Status

Public frontend demo: live at [https://ramiabdu.github.io/Sentineloops/](https://ramiabdu.github.io/Sentineloops/)

Backend API: Not deployed yet. There is no public production API URL in this repository.

As of 2026-05-17, the frontend static demo is deployed with GitHub Pages. The backend API, PostgreSQL, Redis, and worker are deployment-ready but still require an external hosting account and production environment variables.

No secrets are committed. Do not claim a live backend until `/health` returns successfully from a public backend domain.

## Target Deployment

- Free portfolio demo: GitHub Pages frontend
- Frontend: Vercel
- Backend API: Railway
- PostgreSQL: Railway Postgres
- Redis: Railway Redis
- Worker: Railway service
- Free backend preview option: Render web service with Render Postgres and Render Key Value

## Free GitHub Pages Frontend Demo

The repository includes `.github/workflows/pages.yml`, which builds `frontend/dist` and publishes it with GitHub Pages on every push to `main` that changes frontend files or the Pages workflow.

The demo URL is:

```text
https://ramiabdu.github.io/Sentineloops/
```

This is a static dashboard demo. It does not mean the backend API is deployed.

## Local Setup

Create local environment files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Start local infrastructure and services:

```bash
make bootstrap
make up
```

Verify the API:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Required Environment Variables

Backend and worker:

```text
APP_NAME=SentinelOps API
ENVIRONMENT=production
DEBUG=false
PORT=8000
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
DATABASE_ECHO=false
DATABASE_AUTO_MIGRATE=true
REDIS_URL=redis://default:PASSWORD@HOST:PORT/0
CORS_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
AUTH_SECRET_KEY=<generated-secret>
AUTH_TOKEN_TTL_MINUTES=60
AUTH_DEMO_EMAIL=analyst@sentinelops.local
AUTH_DEMO_DISPLAY_NAME=SentinelOps Analyst
AUTH_DEMO_ROLE=admin
```

Frontend:

```text
VITE_API_BASE_URL=https://your-railway-api-domain.up.railway.app
```

Generate a secret:

```bash
openssl rand -hex 32
```

## Railway Deployment

Create Railway services:

1. Create a new Railway project.
2. Add a PostgreSQL service.
3. Add a Redis service.
4. Add a backend API service from this GitHub repository.
5. Add a worker service from the same repository.

Backend API service:

- Builder: Dockerfile
- Dockerfile path: `backend/Dockerfile`
- Start command:

```bash
cd /app/backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

- Health check path: `/health`

Worker service:

- Builder: Dockerfile
- Dockerfile path: `backend/Dockerfile`
- Start command:

```bash
cd /app && PYTHONPATH=/app/backend python -m workers.app.main
```

Set the backend and worker environment variables listed above. Use Railway's generated PostgreSQL and Redis connection strings.

## Free Render Backend Preview

The repository includes `render.yaml` for a free backend API preview on Render:

- Web service: FastAPI backend with Render's Python runtime
- Database: Render Postgres
- Cache/queue: Render Key Value
- Health check: `/health`
- Startup migrations: enabled with `DATABASE_AUTO_MIGRATE=true`

Important limitations:

- This is a portfolio preview path, not a production SLA.
- Render free web services can sleep when idle.
- Render free Postgres has platform limits and expiration behavior; check Render's current free-tier policy before relying on it.
- The worker is not included in the free Render blueprint because Render free instances are for web services and datastores, not background workers.

Render backend commands:

```bash
pip install -r requirements.txt
cd backend && pip install -r requirements.txt
cd backend && alembic upgrade head
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The repository also keeps a root-level `requirements.txt` because Render may fall back to `pip install -r requirements.txt` from the repository root when a service was created manually before the Blueprint was synced.

Manual deployment steps:

1. Sign in to Render.
2. Create a new Blueprint from this GitHub repository.
3. Render will read `render.yaml` from the repository root.
4. Set `CORS_ALLOWED_ORIGINS` to:

```text
https://ramiabdu.github.io
```

5. Deploy the Blueprint.
6. Open the generated Render API URL.
7. Verify:

```bash
curl https://your-render-api.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

After the backend URL is live, set the frontend build variable to that URL if the dashboard starts calling backend APIs:

```text
VITE_API_BASE_URL=https://your-render-api.onrender.com
```

## Vercel Deployment

Create a Vercel project from this GitHub repository.

Recommended project settings:

- Framework preset: Vite
- Install command: `cd frontend && npm install --no-audit --no-fund`
- Build command: `cd frontend && npm run build`
- Output directory: `frontend/dist`

Set:

```text
VITE_API_BASE_URL=https://your-railway-api-domain.up.railway.app
```

After Vercel gives you a public URL, update Railway:

```text
CORS_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
```

## How To Verify Deployment

Backend:

```bash
curl https://your-railway-api-domain.up.railway.app/health
```

Expected:

```json
{"status":"ok"}
```

Frontend:

1. Open the Vercel URL.
2. Confirm the dashboard loads.
3. Confirm browser console has no failed asset loads.
4. Confirm backend requests target `VITE_API_BASE_URL`.

Worker:

1. Trigger a scan through the API or dashboard.
2. Confirm the scan moves from queued to running/completed.
3. Confirm findings are persisted in PostgreSQL.

## Troubleshooting

API fails on startup:

- Check `DATABASE_URL`.
- Confirm Railway Postgres is provisioned and reachable.
- Check Alembic migration logs.

Frontend cannot reach API:

- Check `VITE_API_BASE_URL`.
- Check `CORS_ALLOWED_ORIGINS`.
- Confirm Railway API health check passes.

Worker is idle:

- Confirm `DATABASE_URL` matches the API service.
- Confirm worker start command includes `PYTHONPATH=/app/backend`.
- Confirm queued scans exist.

Auth errors:

- Confirm `AUTH_SECRET_KEY` is set and stable.
- Confirm bearer token is sent as `Authorization: Bearer <token>`.

## Security Notes

- Never commit production `.env` files.
- Rotate `AUTH_SECRET_KEY` if it is exposed.
- Use least-privilege cloud credentials for scanner integrations.
- Keep `DEBUG=false` in production.
- Restrict CORS to the deployed Vercel domain.
