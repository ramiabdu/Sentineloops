from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.scan import Scan
from app.repositories.accounts import get_account
from app.repositories.scans import create_scan
from app.schemas.scan import ScanCreate


class ScanTriggerError(Exception):
    pass


class ScanAccountNotFoundError(ScanTriggerError):
    pass


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
