from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scan import Scan, ScanStatus


def create_scan(
    db: Session,
    *,
    account_id: UUID,
    status: ScanStatus = ScanStatus.QUEUED,
    triggered_by: str | None = None,
) -> Scan:
    scan = Scan(
        account_id=account_id,
        status=status,
        triggered_by=triggered_by,
    )
    db.add(scan)
    return scan


def get_scan(db: Session, scan_id: UUID) -> Scan | None:
    return db.get(Scan, scan_id)


def get_next_queued_scan(db: Session) -> Scan | None:
    statement = (
        select(Scan)
        .where(Scan.status == ScanStatus.QUEUED)
        .order_by(Scan.created_at.asc())
        .limit(1)
    )
    return db.execute(statement).scalar_one_or_none()


def list_scans(
    db: Session,
    *,
    account_id: UUID | None = None,
    status: ScanStatus | None = None,
) -> list[Scan]:
    statement = select(Scan)
    if account_id is not None:
        statement = statement.where(Scan.account_id == account_id)
    if status is not None:
        statement = statement.where(Scan.status == status)

    statement = statement.order_by(Scan.created_at.desc())
    return list(db.execute(statement).scalars().all())
