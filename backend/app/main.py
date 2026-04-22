import logging

from fastapi import FastAPI
from app.api.health import router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting Sentinelops API")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Debug mode: %s", settings.DEBUG)


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "status": "running",
    }


app.include_router(router)
