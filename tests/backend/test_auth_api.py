from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import admin as admin_routes
from app.core.auth import CurrentUser, create_session_token
from app.db import get_db
from app.main import create_application
from app.models import Base
from app.schemas.auth import AuthSignupCreate
from app.services import users as user_service
from app.services.users import UserAlreadyExistsError, register_user


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


def test_signup_creates_public_user():
    client = _build_database_client()

    response = client.post("/auth/signup", json=_signup_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.user@sentinelops.local"
    assert body["display_name"] == "New User"
    assert body["role"] == "admin"
    assert body["subject"] != "new.user@sentinelops.local"


def test_signup_accepts_render_smoke_test_payload_without_display_name():
    client = _build_database_client()

    response = client.post(
        "/auth/signup",
        json={"email": "finaltest@example.com", "password": "12345678"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "finaltest@example.com"
    assert response.json()["display_name"] == "finaltest"


def test_signup_rejects_duplicate_email():
    client = _build_database_client()

    first_response = client.post("/auth/signup", json=_signup_payload())
    duplicate_response = client.post(
        "/auth/signup",
        json={**_signup_payload(), "email": "NEW.USER@SentinelOps.Local"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "code": "user_already_exists",
        "message": "A user with this email already exists.",
    }


def test_signup_validation_errors_return_422():
    client = _build_database_client()

    response = client.post(
        "/auth/signup",
        json={
            "email": "not-an-email",
            "display_name": "Invalid User",
            "password": "short",
            "role": "owner",
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_register_user_rolls_back_after_duplicate_precheck():
    session_factory = _build_session_factory()

    with session_factory() as session:
        register_user(session, AuthSignupCreate(**_signup_payload()))

        with pytest.raises(UserAlreadyExistsError):
            register_user(
                session,
                AuthSignupCreate(
                    **{**_signup_payload(), "email": "NEW.USER@SentinelOps.Local"}
                ),
            )

        second_user = register_user(
            session,
            AuthSignupCreate(
                email="second.user@sentinelops.local",
                display_name="Second User",
                password="correct-password-456",
                role="analyst",
            ),
        )

    assert second_user.email == "second.user@sentinelops.local"


def test_register_user_rolls_back_after_integrity_failure(monkeypatch: pytest.MonkeyPatch):
    session_factory = _build_session_factory()

    with session_factory() as session:
        register_user(session, AuthSignupCreate(**_signup_payload()))
        monkeypatch.setattr(user_service, "get_user_by_email", lambda *_: None)

        with pytest.raises(UserAlreadyExistsError):
            register_user(
                session,
                AuthSignupCreate(
                    **{**_signup_payload(), "email": "NEW.USER@SentinelOps.Local"}
                ),
            )

        monkeypatch.undo()
        second_user = register_user(
            session,
            AuthSignupCreate(
                email="rollback.safe@sentinelops.local",
                display_name="Rollback Safe",
                password="correct-password-789",
                role="analyst",
            ),
        )

    assert second_user.email == "rollback.safe@sentinelops.local"


def test_register_user_rolls_back_after_unexpected_database_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    session_factory = _build_session_factory()

    with session_factory() as session:
        monkeypatch.setattr(user_service, "get_user_by_email", lambda *_: None)
        monkeypatch.setattr(
            session,
            "commit",
            lambda: (_ for _ in ()).throw(
                IntegrityError("insert users", {}, Exception("duplicate email"))
            ),
        )

        with pytest.raises(UserAlreadyExistsError):
            register_user(session, AuthSignupCreate(**_signup_payload()))

        assert not session.in_transaction()


def test_admin_init_db_endpoint_is_hidden_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(admin_routes.settings, "DEBUG_INIT_DB", False)
    monkeypatch.setattr(admin_routes.settings, "ENVIRONMENT", "production")
    client = TestClient(create_application())
    token = client.post("/auth/session").json()["access_token"]

    response = client.post(
        "/admin/init-db",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "admin_init_db_disabled"


def test_admin_init_db_endpoint_runs_when_debug_enabled(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_initialize_database(*, run_migrations: bool, create_missing_tables: bool):
        assert run_migrations is True
        assert create_missing_tables is True
        return SimpleNamespace(
            migrations_checked=True,
            migrations_ran=True,
            missing_tables_checked=True,
            missing_tables_created=True,
        )

    monkeypatch.setattr(admin_routes.settings, "DEBUG_INIT_DB", True)
    monkeypatch.setattr(admin_routes, "initialize_database", fake_initialize_database)
    client = TestClient(create_application())
    token = client.post("/auth/session").json()["access_token"]

    response = client.post(
        "/admin/init-db",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "migrations_checked": True,
        "migrations_ran": True,
        "missing_tables_checked": True,
        "missing_tables_created": True,
    }


def test_login_returns_jwt_for_registered_user_and_auth_me_accepts_it():
    client = _build_database_client()
    client.post("/auth/signup", json=_signup_payload())

    login_response = client.post(
        "/auth/login",
        json={
            "email": "NEW.USER@SentinelOps.Local",
            "password": "correct-password-123",
        },
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2
    assert body["user"]["email"] == "new.user@sentinelops.local"

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == body["user"]


def test_login_rejects_invalid_password():
    client = _build_database_client()
    client.post("/auth/signup", json=_signup_payload())

    response = client.post(
        "/auth/login",
        json={
            "email": "new.user@sentinelops.local",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "authentication_failed",
        "message": "Invalid email or password.",
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
    session_factory = _build_session_factory()
    app = create_application()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


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


def _signup_payload() -> dict[str, str]:
    return {
        "email": "new.user@sentinelops.local",
        "display_name": "New User",
        "password": "correct-password-123",
        "role": "admin",
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
