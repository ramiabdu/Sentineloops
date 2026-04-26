from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting SentinelOps API")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Debug mode: %s", settings.DEBUG)
    yield
