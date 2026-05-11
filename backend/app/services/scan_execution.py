from collections.abc import Callable, Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.base import utc_now
from app.models.scan import Scan, ScanStatus
from app.repositories.scans import get_next_queued_scan, get_scan
from app.scanners import ScannerRunResult, ScanTarget, run_scanners
from app.services.findings import persist_scanner_findings

ScannerRunner = Callable[[ScanTarget], Iterable[ScannerRunResult]]


class ScanExecutionError(Exception):
    pass


class ScanExecutionNotFoundError(ScanExecutionError):
    pass


class ScanNotQueuedError(ScanExecutionError):
    pass


def execute_next_queued_scan(
    db: Session,
    *,
    scanner_runner: ScannerRunner = run_scanners,
) -> Scan | None:
    scan = get_next_queued_scan(db)
    if scan is None:
        return None
    return execute_scan(db, scan.id, scanner_runner=scanner_runner)


def execute_scan(
    db: Session,
    scan_id: UUID,
    *,
    scanner_runner: ScannerRunner = run_scanners,
) -> Scan:
    scan = get_scan(db, scan_id)
    if scan is None:
        raise ScanExecutionNotFoundError(f"Scan was not found: {scan_id}")
    if scan.status != ScanStatus.QUEUED:
        raise ScanNotQueuedError(f"Scan must be queued before execution: {scan_id}")

    _mark_scan_running(db, scan)
    try:
        target = _build_scan_target(scan.account)
        scanner_results = tuple(scanner_runner(target))
        persist_scanner_findings(
            db,
            account_id=scan.account_id,
            scan_id=scan.id,
            scanner_results=scanner_results,
        )
    except Exception as exc:
        db.rollback()
        return _mark_scan_failed(db, scan_id, exc)

    completed_scan = get_scan(db, scan_id)
    if completed_scan is None:
        raise ScanExecutionNotFoundError(f"Scan was not found after execution: {scan_id}")
    _mark_scan_completed(db, completed_scan)
    return completed_scan


def _build_scan_target(account: Account) -> ScanTarget:
    return ScanTarget(
        account_id=account.id,
        cloud_provider=account.cloud_provider,
        external_id=account.external_id,
        account_name=account.name,
    )


def _mark_scan_running(db: Session, scan: Scan) -> None:
    scan.status = ScanStatus.RUNNING
    scan.started_at = utc_now()
    scan.completed_at = None
    scan.error_message = None
    db.commit()
    db.refresh(scan)


def _mark_scan_completed(db: Session, scan: Scan) -> None:
    scan.status = ScanStatus.COMPLETED
    scan.completed_at = utc_now()
    scan.error_message = None
    db.commit()
    db.refresh(scan)


def _mark_scan_failed(db: Session, scan_id: UUID, exc: Exception) -> Scan:
    scan = get_scan(db, scan_id)
    if scan is None:
        raise ScanExecutionNotFoundError(f"Scan was not found after failure: {scan_id}") from exc

    scan.status = ScanStatus.FAILED
    scan.completed_at = utc_now()
    scan.error_message = _format_error_message(exc)
    db.commit()
    db.refresh(scan)
    return scan


def _format_error_message(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    return message[:1000]
