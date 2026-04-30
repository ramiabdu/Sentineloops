from uuid import UUID

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
