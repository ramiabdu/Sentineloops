PROJECT_NAME=sentinelops

.PHONY: help tree bootstrap fmt lint test up down

help:
	@echo "Available targets:"
	@echo "  make tree       - show repo structure"
	@echo "  make bootstrap  - copy .env.example to .env if missing"
	@echo "  make fmt        - format backend code"
	@echo "  make lint       - lint backend code"
	@echo "  make test       - run backend tests"
	@echo "  make up         - start local docker stack"
	@echo "  make down       - stop local docker stack"

tree:
	@find . -maxdepth 3 -type d | sort

bootstrap:
	@test -f .env || cp .env.example .env
	@echo "Environment bootstrapped."

fmt:
	cd backend && python -m black app tests || true
	cd backend && python -m isort app tests || true

lint:
	cd backend && python -m ruff check app tests || true

test:
	cd backend && python -m pytest ../tests/backend -q || true

up:
	docker compose -f docker/docker-compose.yml up --build

down:
	docker compose -f docker/docker-compose.yml down -v
