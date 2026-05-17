# Changelog

## Unreleased

- Added deployment-ready Railway and Vercel configuration.
- Added production-safe backend Docker start command.
- Added backend CORS and Redis environment configuration.
- Added frontend API URL environment configuration.
- Added deployment, security, contribution, roadmap, and GitHub community docs.
- Clarified that the frontend demo is live on GitHub Pages and the backend API is not deployed yet.
- Added a GitHub Pages workflow for the free static frontend demo.
- Added a Render backend preview blueprint for a free API deployment path.
- Normalized hosted Postgres URLs for production providers that expose `postgresql://` or `postgres://` connection strings.
- Switched the Render backend blueprint to the Python runtime with explicit backend build and start commands.
- Added `backend/requirements.txt` for Render's Python dependency installation.
- Added a root-level `requirements.txt` for Render services that run the default Python build command from the repository root.
- Added public user signup, password login, persisted users, and JWT bearer auth support.
- Hardened database session rollback handling for signup/login and enabled production startup migrations.
- Added Render-safe missing-table initialization and a temporary protected `/admin/init-db` endpoint for production debugging.
- Rebuilt the Render backend blueprint around `rootDir: backend`, removed Alembic predeploy startup risk, and made SQLAlchemy missing-table creation the default Render path.
- Made the users Alembic migration tolerant of databases where the `users` table was already created by startup initialization.

## v1.0.0

- Completed 30-day CSPM MVP baseline.
- Added FastAPI backend, scanner plugin architecture, persistence, worker execution model, React dashboard, auth/RBAC foundation, CI, screenshots, and release notes.
