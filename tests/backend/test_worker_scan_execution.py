from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from workers.app.scans import run_once

from app.models import Base
from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.models.scan import ScanStatus
from app.repositories.scans import create_scan, get_scan
from app.scanners import FindingDraft, ScannerRunResult, ScanTarget
from app.schemas.account import AccountCreate
from app.services.accounts import onboard_account


@pytest.fixture()
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)


def test_worker_run_once_executes_one_queued_scan(session_factory: sessionmaker[Session]):
    account_id, scan_id = _create_account_and_scan(session_factory)

    processed_scan = run_once(session_factory, scanner_runner=_successful_runner)

    assert processed_scan is not None
    assert processed_scan.id == scan_id
    assert processed_scan.account_id == account_id
    assert processed_scan.status == ScanStatus.COMPLETED


def test_worker_run_once_returns_none_when_queue_is_empty(
    session_factory: sessionmaker[Session],
):
    assert run_once(session_factory, scanner_runner=_successful_runner) is None


def test_worker_run_once_marks_failed_scan(session_factory: sessionmaker[Session]):
    _, scan_id = _create_account_and_scan(session_factory)

    processed_scan = run_once(session_factory, scanner_runner=_failing_runner)

    assert processed_scan is not None
    assert processed_scan.status == ScanStatus.FAILED
    with session_factory() as session:
        stored_scan = get_scan(session, scan_id)
        assert stored_scan is not None
        assert stored_scan.status == ScanStatus.FAILED
        assert stored_scan.error_message == "provider timeout"


def _create_account_and_scan(session_factory: sessionmaker[Session]):
    with session_factory() as session:
        account = onboard_account(
            session,
            AccountCreate(
                name="AWS production",
                cloud_provider=CloudProvider.AWS,
                external_id="123456789012",
            ),
        )
        scan = create_scan(session, account_id=account.id, triggered_by="tests")
        session.commit()
        session.refresh(scan)
        return account.id, scan.id


def _successful_runner(_: ScanTarget) -> tuple[ScannerRunResult, ...]:
    return (
        ScannerRunResult(
            scanner_name="test-worker-scanner",
            findings=(
                FindingDraft(
                    severity=FindingSeverity.LOW,
                    title="Worker test finding",
                    description="Worker test finding description.",
                    resource_id="worker-test",
                    resource_type="test_resource",
                ),
            ),
        ),
    )


def _failing_runner(_: ScanTarget) -> tuple[ScannerRunResult, ...]:
    raise RuntimeError("provider timeout")
