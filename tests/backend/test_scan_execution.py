from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.models.scan import ScanStatus
from app.repositories.findings import list_findings_for_scan
from app.repositories.scans import create_scan
from app.scanners import FindingDraft, ScannerRunResult, ScanTarget
from app.schemas.account import AccountCreate
from app.services.accounts import onboard_account
from app.services.scan_execution import ScanNotQueuedError, execute_next_queued_scan, execute_scan


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        yield session


def test_execute_scan_persists_results_and_marks_completed(db_session: Session):
    account = _create_account(db_session)
    scan = create_scan(db_session, account_id=account.id, triggered_by="tests")
    db_session.commit()
    db_session.refresh(scan)

    executed_scan = execute_scan(db_session, scan.id, scanner_runner=_successful_runner)
    findings = list_findings_for_scan(db_session, scan.id)

    assert executed_scan.status == ScanStatus.COMPLETED
    assert executed_scan.started_at is not None
    assert executed_scan.completed_at is not None
    assert executed_scan.error_message is None
    assert len(findings) == 1
    assert findings[0].scan_id == scan.id
    assert findings[0].account_id == account.id
    assert findings[0].scanner_name == "test-security-group-scanner"
    assert findings[0].risk_score is not None


def test_execute_scan_marks_failed_when_runner_errors(db_session: Session):
    account = _create_account(db_session)
    scan = create_scan(db_session, account_id=account.id, triggered_by="tests")
    db_session.commit()
    db_session.refresh(scan)

    executed_scan = execute_scan(db_session, scan.id, scanner_runner=_failing_runner)

    assert executed_scan.status == ScanStatus.FAILED
    assert executed_scan.started_at is not None
    assert executed_scan.completed_at is not None
    assert executed_scan.error_message == "scanner credentials are unavailable"
    assert list_findings_for_scan(db_session, scan.id) == []


def test_execute_next_queued_scan_processes_oldest_scan(db_session: Session):
    first_account = _create_account(db_session, external_id="123456789012")
    second_account = _create_account(db_session, external_id="210987654321")
    first_scan = create_scan(db_session, account_id=first_account.id, triggered_by="tests")
    second_scan = create_scan(db_session, account_id=second_account.id, triggered_by="tests")
    db_session.commit()

    executed_scan = execute_next_queued_scan(db_session, scanner_runner=_successful_runner)
    db_session.refresh(second_scan)

    assert executed_scan is not None
    assert executed_scan.id == first_scan.id
    assert executed_scan.status == ScanStatus.COMPLETED
    assert second_scan.status == ScanStatus.QUEUED


def test_execute_scan_rejects_non_queued_scan(db_session: Session):
    account = _create_account(db_session)
    scan = create_scan(
        db_session,
        account_id=account.id,
        status=ScanStatus.RUNNING,
        triggered_by="tests",
    )
    db_session.commit()
    db_session.refresh(scan)

    with pytest.raises(ScanNotQueuedError):
        execute_scan(db_session, scan.id, scanner_runner=_successful_runner)


def _create_account(
    db_session: Session,
    *,
    external_id: str = "123456789012",
):
    return onboard_account(
        db_session,
        AccountCreate(
            name="AWS production",
            cloud_provider=CloudProvider.AWS,
            external_id=external_id,
        ),
    )


def _successful_runner(target: ScanTarget) -> tuple[ScannerRunResult, ...]:
    assert target.cloud_provider == CloudProvider.AWS
    return (
        ScannerRunResult(
            scanner_name="test-security-group-scanner",
            findings=(
                FindingDraft(
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
            ),
        ),
    )


def _failing_runner(_: ScanTarget) -> tuple[ScannerRunResult, ...]:
    raise RuntimeError("scanner credentials are unavailable")
