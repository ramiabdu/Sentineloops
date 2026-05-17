from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.core.auth import ROLE_ADMIN, CurrentUser, require_roles
from app.core.config import settings
from app.core.errors import NotFoundError
from app.db import initialize_database

router = APIRouter(prefix="/admin", tags=["admin"])


class InitDbResponse(BaseModel):
    status: str
    migrations_checked: bool
    migrations_ran: bool
    missing_tables_checked: bool
    missing_tables_created: bool


@router.post(
    "/init-db",
    response_model=InitDbResponse,
    status_code=status.HTTP_200_OK,
)
def init_db(
    _: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
) -> InitDbResponse:
    if not settings.is_debug_init_db_enabled:
        raise NotFoundError(
            code="admin_init_db_disabled",
            message="Database initialization endpoint is disabled.",
        )

    result = initialize_database(run_migrations=True, create_missing_tables=True)
    return InitDbResponse(status="ok", **result.__dict__)
