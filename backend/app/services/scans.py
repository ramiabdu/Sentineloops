from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import utc_now
from app.models.finding import FindingSeverity, FindingStatus
from app.models.scan import Scan
from app.repositories.accounts import get_account
from app.repositories.findings import (
    count_findings_for_scan,
    count_findings_for_scan_by_severity,
    count_findings_for_scan_by_status,
)
from app.repositories.scans import create_scan, get_scan
from app.schemas.scan import ScanCreate


class ScanTriggerError(Exception):
    pass


class ScanAccountNotFoundError(ScanTriggerError):
    pass


class ScanStatusNotFoundError(ScanTriggerError):
    pass


@dataclass(frozen=True)
class ScanStatusSnapshot:
    id: UUID
    account_id: UUID
    status: str
    triggered_by: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    duration_seconds: int | None
    findings_total: int
    findings_by_severity: dict[str, int]
    findings_by_status: dict[str, int]


def trigger_scan(db: Session, payload: ScanCreate) -> Scan:
    account = get_account(db, payload.account_id)
    if account is None:
        raise ScanAccountNotFoundError()

    scan = create_scan(
        db,
        account_id=account.id,
        triggered_by=payload.triggered_by,
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ScanTriggerError from exc

    db.refresh(scan)
    return scan


def get_scan_status_snapshot(db: Session, scan_id: UUID) -> ScanStatusSnapshot:
    scan = get_scan(db, scan_id)
    if scan is None:
        raise ScanStatusNotFoundError()

    severity_counts = count_findings_for_scan_by_severity(db, scan.id)
    status_counts = count_findings_for_scan_by_status(db, scan.id)

    return ScanStatusSnapshot(
        id=scan.id,
        account_id=scan.account_id,
        status=scan.status.value,
        triggered_by=scan.triggered_by,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        duration_seconds=_scan_duration_seconds(scan),
        findings_total=count_findings_for_scan(db, scan.id),
        findings_by_severity=_complete_enum_counts(FindingSeverity, severity_counts),
        findings_by_status=_complete_enum_counts(FindingStatus, status_counts),
    )


def _scan_duration_seconds(scan: Scan) -> int | None:
    if scan.started_at is None:
        return None

    end_time = scan.completed_at or utc_now()
    started_at, end_time = _normalize_datetimes(scan.started_at, end_time)
    return max(0, int((end_time - started_at).total_seconds()))


def _normalize_datetimes(
    started_at: datetime,
    end_time: datetime,
) -> tuple[datetime, datetime]:
    if started_at.tzinfo is None and end_time.tzinfo is not None:
        end_time = end_time.replace(tzinfo=None)
    elif started_at.tzinfo is not None and end_time.tzinfo is None:
        started_at = started_at.replace(tzinfo=None)
    return started_at, end_time


def _complete_enum_counts(enum_class: type, counts: dict[object, int]) -> dict[str, int]:
    normalized_counts = {_enum_value(key): count for key, count in counts.items()}
    return {member.value: normalized_counts.get(member.value, 0) for member in enum_class}


def _enum_value(value: object) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)
