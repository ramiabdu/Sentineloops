from fastapi import APIRouter, Depends

from app.api.routes.accounts import router as accounts_router
from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.findings import router as findings_router
from app.api.routes.health import router as health_router
from app.api.routes.scans import router as scans_router
from app.core.auth import get_current_user

api_router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(accounts_router)
protected_router.include_router(findings_router)
protected_router.include_router(scans_router)

api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(protected_router)
api_router.include_router(health_router, tags=["health"])
