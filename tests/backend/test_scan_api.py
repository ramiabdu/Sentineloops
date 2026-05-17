from collections.abc import Generator
from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import CurrentUser, get_current_user
from app.db import get_db
from app.main import create_application
from app.models import Base
from app.models.finding import FindingSeverity
from app.models.scan import ScanStatus
from app.repositories.scans import create_scan
from app.scanners import FindingDraft
from app.services.findings import persist_finding_draft


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
    app.state.session_factory = session_factory

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    def override_current_user() -> CurrentUser:
        return CurrentUser(
            subject="test-user",
            email="test@example.com",
            display_name="Test User",
            role="admin",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

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


def test_get_scan_status_returns_tracking_summary(client: TestClient):
    account_id = _create_account(client)
    scan_id = _create_completed_scan(client, account_id)
    _create_security_group_finding(client, account_id, scan_id)
    _create_s3_finding(client, account_id, scan_id)

    response = client.get(f"/scans/{scan_id}/status")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == scan_id
    assert body["account_id"] == account_id
    assert body["status"] == "completed"
    assert body["duration_seconds"] == 300
    assert body["findings_total"] == 2
    assert body["findings_by_severity"] == {
        "critical": 1,
        "high": 1,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    assert body["findings_by_status"] == {
        "open": 2,
        "triaged": 0,
        "resolved": 0,
    }


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


def test_missing_scan_status_returns_standard_not_found_error(client: TestClient):
    response = client.get("/scans/00000000-0000-0000-0000-000000000001/status")

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


def _create_completed_scan(client: TestClient, account_id: str) -> str:
    with client.app.state.session_factory() as session:
        scan = create_scan(
            session,
            account_id=UUID(account_id),
            status=ScanStatus.COMPLETED,
            triggered_by="api-test",
        )
        scan.started_at = datetime(2026, 5, 12, 12, 0, tzinfo=timezone.utc)
        scan.completed_at = datetime(2026, 5, 12, 12, 5, tzinfo=timezone.utc)
        session.commit()
        session.refresh(scan)
        return str(scan.id)


def _create_security_group_finding(client: TestClient, account_id: str, scan_id: str) -> str:
    with client.app.state.session_factory() as session:
        finding = persist_finding_draft(
            session,
            account_id=UUID(account_id),
            scan_id=UUID(scan_id),
            scanner_name="aws-security-group-open-port",
            draft=FindingDraft(
                severity=FindingSeverity.CRITICAL,
                title="Security group allows public ingress",
                description="Public SSH ingress is allowed.",
                resource_id="sg-123",
                resource_type="security_group",
                region="us-east-1",
                metadata={
                    "source": "0.0.0.0/0",
                    "exposes_admin_port": True,
                },
            ),
        )
        return str(finding.id)


def _create_s3_finding(client: TestClient, account_id: str, scan_id: str) -> str:
    with client.app.state.session_factory() as session:
        finding = persist_finding_draft(
            session,
            account_id=UUID(account_id),
            scan_id=UUID(scan_id),
            scanner_name="aws-s3-public-bucket",
            draft=FindingDraft(
                severity=FindingSeverity.HIGH,
                title="S3 bucket ACL grants public access",
                description="The bucket ACL includes public grants.",
                resource_id="arn:aws:s3:::public-assets",
                resource_type="s3_bucket",
                region="us-east-1",
                metadata={
                    "bucket_name": "public-assets",
                    "detection_source": "bucket_acl",
                    "blocks_all_public_access": False,
                },
            ),
        )
        return str(finding.id)
