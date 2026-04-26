PROJECT_NAME=sentinelops

.PHONY: help tree bootstrap run-backend db-bootstrap db-current fmt lint test up logs down

help:
	@echo "Available targets:"
	@echo "  make tree       - show repo structure"
	@echo "  make bootstrap  - copy backend/.env.example to backend/.env if missing"
	@echo "  make run-backend - start backend API locally"
	@echo "  make db-bootstrap - apply all Alembic migrations"
	@echo "  make db-current  - show current Alembic revision"
	@echo "  make fmt        - format backend code"
	@echo "  make lint       - lint backend code"
	@echo "  make test       - run backend tests"
	@echo "  make up         - build and start local docker stack"
	@echo "  make logs       - stream docker service logs"
	@echo "  make down       - stop local docker stack"

tree:
	@find . -maxdepth 3 -type d | sort

bootstrap:
	@test -f backend/.env || cp backend/.env.example backend/.env
	@echo "Environment bootstrapped."

run-backend:
	cd backend && python -m uvicorn app.main:app --reload

db-bootstrap:
	cd backend && alembic upgrade head

db-current:
	cd backend && alembic current

fmt:
	cd backend && python -m black app ../tests
	cd backend && python -m isort app ../tests

lint:
	cd backend && python -m ruff check app ../tests

test:
	cd backend && python -m pytest ../tests/backend -q

up: bootstrap
	docker compose -f docker/docker-compose.yml up --build

logs:
	docker compose -f docker/docker-compose.yml logs -f

down:
	docker compose -f docker/docker-compose.yml down -v
