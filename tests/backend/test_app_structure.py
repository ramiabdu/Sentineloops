from app.core.config import settings
from app.main import create_application


def test_application_factory_registers_core_routes():
    app = create_application()
    route_paths = {route.path for route in app.routes}

    assert "/" in route_paths
    assert "/accounts" in route_paths
    assert "/accounts/{account_id}" in route_paths
    assert "/health" in route_paths
    assert app.title == settings.APP_NAME
