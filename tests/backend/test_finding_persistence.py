from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from app.models.account import CloudProvider
from app.models.finding import FindingSeverity, FindingStatus
from app.models.scan import ScanStatus
from app.repositories.findings import list_findings_for_account, list_findings_for_scan
from app.repositories.scans import create_scan
from app.scanners import FindingDraft, ScannerRunResult
from app.schemas.account import AccountCreate
from app.services.accounts import onboard_account
from app.services.findings import persist_finding_draft, persist_scanner_findings


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        yield session


def create_test_account(db_session: Session):
    return onboard_account(
        db_session,
        AccountCreate(
            name="AWS production",
            cloud_provider=CloudProvider.AWS,
            external_id="123456789012",
        ),
    )


def test_persist_single_finding_draft(db_session: Session):
    account = create_test_account(db_session)
    draft = FindingDraft(
        severity=FindingSeverity.HIGH,
        title="Public S3 bucket",
        description="Bucket policy allows public access.",
        resource_id="arn:aws:s3:::public-assets",
        resource_type="s3_bucket",
        region="us-east-1",
        remediation="Restrict the bucket policy.",
        risk_score=Decimal("7.135"),
        metadata={
            "bucket_name": "public-assets",
            "public_acl_grants": ("AllUsers:READ",),
        },
    )

    finding = persist_finding_draft(
        db_session,
        account_id=account.id,
        scanner_name="aws-s3-public-bucket",
        draft=draft,
    )

    assert finding.id is not None
    assert finding.account_id == account.id
    assert finding.scan_id is None
    assert finding.status == FindingStatus.OPEN
    assert finding.severity == FindingSeverity.HIGH
    assert finding.scanner_name == "aws-s3-public-bucket"
    assert finding.resource_metadata == {
        "bucket_name": "public-assets",
        "public_acl_grants": ["AllUsers:READ"],
    }
    assert finding.risk_score == Decimal("7.14")


def test_persist_scanner_findings_links_to_scan(db_session: Session):
    account = create_test_account(db_session)
    scan = create_scan(
        db_session,
        account_id=account.id,
        status=ScanStatus.RUNNING,
        triggered_by="tests",
    )
    db_session.commit()
    db_session.refresh(scan)
    scanner_results = [
        ScannerRunResult(
            scanner_name="aws-security-group-open-port",
            findings=(
                FindingDraft(
                    severity=FindingSeverity.CRITICAL,
                    title="Security group allows public ingress",
                    description="Public SSH ingress is allowed.",
                    resource_id="sg-123",
                    resource_type="security_group",
                    region="us-east-1",
                    metadata={"source": "0.0.0.0/0", "port_label": "22"},
                ),
            ),
        ),
        ScannerRunResult(
            scanner_name="aws-iam-user-without-mfa",
            findings=(
                FindingDraft(
                    severity=FindingSeverity.HIGH,
                    title="IAM user console access has no MFA",
                    description="Console access lacks MFA.",
                    resource_id="arn:aws:iam::123456789012:user/alice",
                    resource_type="iam_user",
                    metadata={"user_name": "alice"},
                ),
            ),
        ),
    ]

    findings = persist_scanner_findings(
        db_session,
        account_id=account.id,
        scan_id=scan.id,
        scanner_results=scanner_results,
    )

    assert len(findings) == 2
    assert {finding.scan_id for finding in findings} == {scan.id}
    assert {finding.account_id for finding in findings} == {account.id}
    assert {finding.scanner_name for finding in findings} == {
        "aws-security-group-open-port",
        "aws-iam-user-without-mfa",
    }
    assert len(list_findings_for_scan(db_session, scan.id)) == 2
    assert len(list_findings_for_account(db_session, account.id)) == 2


def test_persist_scanner_findings_commits_empty_results(db_session: Session):
    account = create_test_account(db_session)

    findings = persist_scanner_findings(
        db_session,
        account_id=account.id,
        scanner_results=[
            ScannerRunResult(scanner_name="aws-s3-public-bucket", findings=())
        ],
    )

    assert findings == []
    assert list_findings_for_account(db_session, account.id) == []
