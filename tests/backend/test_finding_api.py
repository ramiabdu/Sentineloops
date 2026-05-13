from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import create_application
from app.models import Base
from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.models.scan import ScanStatus
from app.repositories.scans import create_scan
from app.scanners import FindingDraft
from app.schemas.account import AccountCreate
from app.services.accounts import onboard_account
from app.services.findings import persist_finding_draft

ClientSessionFactory = tuple[TestClient, sessionmaker[Session]]


@pytest.fixture()
def client_with_session_factory() -> Generator[ClientSessionFactory, None, None]:
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
        yield test_client, session_factory

    app.dependency_overrides.clear()


def test_list_findings_returns_persisted_findings(
    client_with_session_factory: ClientSessionFactory,
):
    client, session_factory = client_with_session_factory
    account_id = _create_test_account(session_factory)
    security_group_finding_id = _create_security_group_finding(session_factory, account_id)
    s3_finding_id = _create_s3_finding(session_factory, account_id)

    response = client.get("/findings")

    assert response.status_code == 200
    findings = response.json()
    assert {finding["id"] for finding in findings} == {
        str(security_group_finding_id),
        str(s3_finding_id),
    }
    security_group_finding = _find_response_by_resource_type(findings, "security_group")
    assert security_group_finding["account_id"] == str(account_id)
    assert security_group_finding["severity"] == "critical"
    assert security_group_finding["status"] == "open"
    assert security_group_finding["risk_score"] == "10.00"
    assert security_group_finding["resource_metadata"]["exposes_admin_port"] is True


def test_list_findings_applies_query_filters(
    client_with_session_factory: ClientSessionFactory,
):
    client, session_factory = client_with_session_factory
    account_id = _create_test_account(session_factory)
    scan_id = _create_test_scan(session_factory, account_id)
    _create_security_group_finding(session_factory, account_id, scan_id=scan_id)
    _create_s3_finding(session_factory, account_id)

    response = client.get(
        "/findings",
        params={
            "account_id": str(account_id),
            "scan_id": str(scan_id),
            "severity": "critical",
            "status": "open",
            "scanner_name": "aws-security-group-open-port",
        },
    )

    assert response.status_code == 200
    findings = response.json()
    assert len(findings) == 1
    assert findings[0]["resource_type"] == "security_group"
    assert findings[0]["scanner_name"] == "aws-security-group-open-port"


def test_get_finding_by_id_returns_detail(
    client_with_session_factory: ClientSessionFactory,
):
    client, session_factory = client_with_session_factory
    account_id = _create_test_account(session_factory)
    finding_id = _create_s3_finding(session_factory, account_id)

    response = client.get(f"/findings/{finding_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(finding_id)
    assert body["resource_type"] == "s3_bucket"
    assert body["risk_score"] == "7.75"
    assert body["resource_metadata"]["detection_source"] == "bucket_acl"
    assert body["first_seen_at"]
    assert body["last_seen_at"]
    assert body["occurrence_count"] == 1


def test_missing_finding_returns_standard_not_found_error(
    client_with_session_factory: ClientSessionFactory,
):
    client, _ = client_with_session_factory

    response = client.get("/findings/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
    assert response.json() == {
        "code": "finding_not_found",
        "message": "Finding was not found.",
    }


def _create_test_account(session_factory: sessionmaker[Session]) -> UUID:
    with session_factory() as session:
        account = onboard_account(
            session,
            AccountCreate(
                name="AWS production",
                cloud_provider=CloudProvider.AWS,
                external_id="123456789012",
            ),
        )
        session.commit()
        session.refresh(account)
        return account.id


def _create_test_scan(session_factory: sessionmaker[Session], account_id: UUID) -> UUID:
    with session_factory() as session:
        scan = create_scan(
            session,
            account_id=account_id,
            status=ScanStatus.RUNNING,
            triggered_by="tests",
        )
        session.commit()
        session.refresh(scan)
        return scan.id


def _create_security_group_finding(
    session_factory: sessionmaker[Session],
    account_id: UUID,
    *,
    scan_id: UUID | None = None,
) -> UUID:
    with session_factory() as session:
        finding = persist_finding_draft(
            session,
            account_id=account_id,
            scan_id=scan_id,
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
                    "port_label": "22",
                    "exposes_admin_port": True,
                },
            ),
        )
        return finding.id


def _create_s3_finding(session_factory: sessionmaker[Session], account_id: UUID) -> UUID:
    with session_factory() as session:
        finding = persist_finding_draft(
            session,
            account_id=account_id,
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
        return finding.id


def _find_response_by_resource_type(
    findings: list[dict[str, object]],
    resource_type: str,
) -> dict[str, object]:
    return next(finding for finding in findings if finding["resource_type"] == resource_type)
