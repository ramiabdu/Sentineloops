from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db import get_db
from app.models.scan import ScanStatus
from app.repositories.scans import get_scan, list_scans
from app.schemas.scan import ScanCreate, ScanResponse
from app.services.scans import ScanAccountNotFoundError, trigger_scan

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
def create_scan(payload: ScanCreate, db: Session = Depends(get_db)) -> ScanResponse:
    try:
        scan = trigger_scan(db, payload)
    except ScanAccountNotFoundError as exc:
        raise NotFoundError(
            code="scan_account_not_found",
            message="Cloud account for scan was not found.",
        ) from exc

    return ScanResponse.model_validate(scan)


@router.get("", response_model=list[ScanResponse])
def get_scans(
    account_id: UUID | None = Query(default=None),
    scan_status: ScanStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[ScanResponse]:
    scans = list_scans(db, account_id=account_id, status=scan_status)
    return [ScanResponse.model_validate(scan) for scan in scans]


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_by_id(scan_id: UUID, db: Session = Depends(get_db)) -> ScanResponse:
    scan = get_scan(db, scan_id)
    if scan is None:
        raise NotFoundError(
            code="scan_not_found",
            message="Scan was not found.",
        )

    return ScanResponse.model_validate(scan)
