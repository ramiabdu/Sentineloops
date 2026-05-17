from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.main import create_application


def test_application_factory_registers_core_routes():
    app = create_application()
    route_paths = {route.path for route in app.routes}

    assert "/" in route_paths
    assert "/accounts" in route_paths
    assert "/accounts/{account_id}" in route_paths
    assert "/auth/session" in route_paths
    assert "/auth/me" in route_paths
    assert "/health" in route_paths
    assert app.title == settings.APP_NAME


def test_application_registers_cors_middleware():
    app = create_application()

    assert any(middleware.cls is CORSMiddleware for middleware in app.user_middleware)
    assert "http://localhost:5173" in settings.cors_allowed_origins
