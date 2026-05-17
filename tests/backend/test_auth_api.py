from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.auth import CurrentUser, create_session_token
from app.main import create_application


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
