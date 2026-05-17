from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.core.config import BACKEND_DIR, settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting SentinelOps API")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Debug mode: %s", settings.DEBUG)
    if settings.should_run_database_migrations:
        run_database_migrations()
    yield


def run_database_migrations() -> None:
    logger.info("Running database migrations")
    alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(alembic_config, "head")
