from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import CurrentUser, create_session_token
from app.db import get_db
from app.main import create_application
from app.models import Base


def test_auth_session_returns_bearer_token_for_mock_user():
    client = TestClient(create_application())

    response = client.post(
        "/auth/session",
        json={
            "email": "Analyst@SentinelOps.Local",
            "display_name": "Security Analyst",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert body["access_token"].count(".") == 2
    assert body["user"] == {
        "subject": "analyst@sentinelops.local",
        "email": "analyst@sentinelops.local",
        "display_name": "Security Analyst",
        "role": "admin",
    }


def test_auth_session_rejects_unknown_role():
    client = TestClient(create_application())

    response = client.post(
        "/auth/session",
        json={
            "email": "owner@sentinelops.local",
            "display_name": "Owner",
            "role": "owner",
        },
    )

    assert response.status_code == 422


def test_auth_me_returns_current_user_from_bearer_token():
    client = TestClient(create_application())
    session_response = client.post("/auth/session")
    access_token = session_response.json()["access_token"]

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert response.json() == session_response.json()["user"]


def test_protected_routes_require_bearer_token_before_database_access():
    client = TestClient(create_application())

    response = client.get("/accounts")

    assert response.status_code == 401
    assert response.json() == {
        "code": "authentication_failed",
        "message": "Valid bearer authentication is required.",
    }


def test_auth_me_rejects_invalid_token():
    client = TestClient(create_application())

    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid.token.value"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"


def test_viewer_can_read_accounts():
    client = _build_database_client()
    headers = _auth_headers(client, role="viewer")

    response = client.get("/accounts", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_viewer_cannot_create_account():
    client = _build_database_client()
    headers = _auth_headers(client, role="viewer")

    response = client.post("/accounts", headers=headers, json=_account_payload())

    assert response.status_code == 403
    assert response.json() == {
        "code": "authorization_failed",
        "message": "User role is not allowed to perform this action.",
    }


def test_analyst_cannot_create_account():
    client = _build_database_client()
    headers = _auth_headers(client, role="analyst")

    response = client.post("/accounts", headers=headers, json=_account_payload())

    assert response.status_code == 403
    assert response.json()["code"] == "authorization_failed"


def test_admin_can_create_account():
    client = _build_database_client()
    headers = _auth_headers(client, role="admin")

    response = client.post("/accounts", headers=headers, json=_account_payload())

    assert response.status_code == 201
    assert response.json()["name"] == "AWS production"


def test_analyst_can_reach_scan_trigger_after_rbac_check():
    client = _build_database_client()
    headers = _auth_headers(client, role="analyst")

    response = client.post(
        "/scans",
        headers=headers,
        json={"account_id": str(uuid4()), "triggered_by": "analyst"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "scan_account_not_found"


def test_viewer_cannot_trigger_scan():
    client = _build_database_client()
    headers = _auth_headers(client, role="viewer")

    response = client.post(
        "/scans",
        headers=headers,
        json={"account_id": str(uuid4()), "triggered_by": "viewer"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "authorization_failed"


def _build_database_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_application()

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _auth_headers(client: TestClient, *, role: str) -> dict[str, str]:
    response = client.post(
        "/auth/session",
        json={
            "email": f"{role}@sentinelops.local",
            "display_name": role.title(),
            "role": role,
        },
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def _account_payload() -> dict[str, str]:
    return {
        "name": "AWS production",
        "cloud_provider": "aws",
        "external_id": "123456789012",
    }


def test_auth_me_rejects_expired_token():
    client = TestClient(create_application())
    issued_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = create_session_token(
        CurrentUser(
            subject="expired@example.com",
            email="expired@example.com",
            display_name="Expired User",
            role="admin",
        ),
        now=issued_at,
        ttl_minutes=1,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"
