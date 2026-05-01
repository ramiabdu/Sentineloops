from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db import get_db
from app.models.finding import FindingSeverity, FindingStatus
from app.repositories.findings import get_finding, list_findings
from app.schemas.finding import FindingResponse

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("", response_model=list[FindingResponse])
def get_findings(
    account_id: UUID | None = Query(default=None),
    scan_id: UUID | None = Query(default=None),
    severity: FindingSeverity | None = Query(default=None),
    status: FindingStatus | None = Query(default=None),
    scanner_name: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> list[FindingResponse]:
    findings = list_findings(
        db,
        account_id=account_id,
        scan_id=scan_id,
        severity=severity,
        status=status,
        scanner_name=scanner_name,
    )
    return [FindingResponse.model_validate(finding) for finding in findings]


@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding_by_id(finding_id: UUID, db: Session = Depends(get_db)) -> FindingResponse:
    finding = get_finding(db, finding_id)
    if finding is None:
        raise NotFoundError(
            code="finding_not_found",
            message="Finding was not found.",
        )

    return FindingResponse.model_validate(finding)
