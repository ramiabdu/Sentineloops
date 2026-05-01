from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finding import Finding, FindingSeverity, FindingStatus


def create_finding(
    db: Session,
    *,
    account_id: UUID,
    scanner_name: str,
    severity: FindingSeverity,
    title: str,
    description: str,
    resource_id: str,
    resource_type: str,
    scan_id: UUID | None = None,
    region: str | None = None,
    risk_score: Decimal | None = None,
    remediation: str | None = None,
    resource_metadata: dict[str, object] | None = None,
) -> Finding:
    finding = Finding(
        account_id=account_id,
        scan_id=scan_id,
        severity=severity,
        title=title,
        description=description,
        resource_id=resource_id,
        resource_type=resource_type,
        region=region,
        scanner_name=scanner_name,
        risk_score=risk_score,
        remediation=remediation,
        resource_metadata=resource_metadata,
    )
    db.add(finding)
    return finding


def get_finding(db: Session, finding_id: UUID) -> Finding | None:
    return db.get(Finding, finding_id)


def list_findings(
    db: Session,
    *,
    account_id: UUID | None = None,
    scan_id: UUID | None = None,
    severity: FindingSeverity | None = None,
    status: FindingStatus | None = None,
    scanner_name: str | None = None,
) -> list[Finding]:
    statement = select(Finding)
    if account_id is not None:
        statement = statement.where(Finding.account_id == account_id)
    if scan_id is not None:
        statement = statement.where(Finding.scan_id == scan_id)
    if severity is not None:
        statement = statement.where(Finding.severity == severity)
    if status is not None:
        statement = statement.where(Finding.status == status)
    if scanner_name is not None:
        statement = statement.where(Finding.scanner_name == scanner_name)

    statement = statement.order_by(Finding.created_at.desc())
    return list(db.execute(statement).scalars().all())


def list_findings_for_account(db: Session, account_id: UUID) -> list[Finding]:
    statement = (
        select(Finding).where(Finding.account_id == account_id).order_by(Finding.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())


def list_findings_for_scan(db: Session, scan_id: UUID) -> list[Finding]:
    statement = (
        select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.created_at.desc())
    )
    return list(db.execute(statement).scalars().all())
