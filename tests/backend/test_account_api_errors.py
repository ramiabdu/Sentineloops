from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import create_application
from app.models import Base


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_application()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_duplicate_account_returns_standard_conflict_error(client: TestClient):
    payload = {
        "name": "AWS production",
        "cloud_provider": "aws",
        "external_id": "123456789012",
    }

    first_response = client.post("/accounts", json=payload)
    duplicate_response = client.post("/accounts", json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "code": "account_already_exists",
        "message": "Cloud account is already onboarded.",
    }


def test_missing_account_returns_standard_not_found_error(client: TestClient):
    response = client.get("/accounts/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
    assert response.json() == {
        "code": "account_not_found",
        "message": "Cloud account was not found.",
    }


def test_invalid_account_payload_returns_standard_validation_error(client: TestClient):
    response = client.post(
        "/accounts",
        json={
            "name": "   ",
            "cloud_provider": "aws",
            "external_id": "bad id",
        },
    )

    body = response.json()
    detail_locations = {tuple(detail["loc"]) for detail in body["details"]}

    assert response.status_code == 422
    assert body["code"] == "validation_error"
    assert body["message"] == "Request validation failed."
    assert ("body", "name") in detail_locations
    assert ("body", "external_id") in detail_locations
