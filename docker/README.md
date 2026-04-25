# Docker

Local development stack definitions live here.

## Services

- `api`: FastAPI app with Alembic bootstrap on startup
- `db`: PostgreSQL 16
- `redis`: Redis 7

## Usage

From the repository root:

```bash
make bootstrap
make up
```

To follow the running services:

```bash
make logs
```

Once the stack is running:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
