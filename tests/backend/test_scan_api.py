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


def test_trigger_scan_creates_queued_scan(client: TestClient):
    account_id = _create_account(client)

    response = client.post(
        "/scans",
        json={
            "account_id": account_id,
            "triggered_by": "api-test",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["id"]
    assert body["account_id"] == account_id
    assert body["status"] == "queued"
    assert body["triggered_by"] == "api-test"
    assert body["started_at"] is None
    assert body["completed_at"] is None
    assert body["error_message"] is None


def test_list_scans_applies_account_and_status_filters(client: TestClient):
    first_account_id = _create_account(client, name="AWS production", external_id="123456789012")
    second_account_id = _create_account(client, name="AWS staging", external_id="210987654321")
    first_scan_id = _trigger_scan(client, first_account_id)
    _trigger_scan(client, second_account_id)

    response = client.get(
        "/scans",
        params={
            "account_id": first_account_id,
            "status": "queued",
        },
    )

    assert response.status_code == 200
    scans = response.json()
    assert len(scans) == 1
    assert scans[0]["id"] == first_scan_id
    assert scans[0]["account_id"] == first_account_id
    assert scans[0]["status"] == "queued"


def test_get_scan_by_id_returns_status(client: TestClient):
    account_id = _create_account(client)
    scan_id = _trigger_scan(client, account_id)

    response = client.get(f"/scans/{scan_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == scan_id
    assert body["account_id"] == account_id
    assert body["status"] == "queued"


def test_trigger_scan_rejects_missing_account(client: TestClient):
    response = client.post(
        "/scans",
        json={
            "account_id": "00000000-0000-0000-0000-000000000001",
            "triggered_by": "api-test",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "scan_account_not_found",
        "message": "Cloud account for scan was not found.",
    }


def test_missing_scan_returns_standard_not_found_error(client: TestClient):
    response = client.get("/scans/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
    assert response.json() == {
        "code": "scan_not_found",
        "message": "Scan was not found.",
    }


def _create_account(
    client: TestClient,
    *,
    name: str = "AWS production",
    external_id: str = "123456789012",
) -> str:
    response = client.post(
        "/accounts",
        json={
            "name": name,
            "cloud_provider": "aws",
            "external_id": external_id,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _trigger_scan(client: TestClient, account_id: str) -> str:
    response = client.post(
        "/scans",
        json={
            "account_id": account_id,
            "triggered_by": "api-test",
        },
    )
    assert response.status_code == 202
    return response.json()["id"]
