from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse, RootResponse

router = APIRouter()


@router.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(
        service=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        status="running",
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
