from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.lifecycle import lifespan
from app.core.logging import configure_logging

configure_logging()


def create_application() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
    app.include_router(api_router)
    return app


app = create_application()
