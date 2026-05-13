from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
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
    seen_at: datetime,
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
        first_seen_at=seen_at,
        last_seen_at=seen_at,
        occurrence_count=1,
    )
    db.add(finding)
    return finding


def get_finding(db: Session, finding_id: UUID) -> Finding | None:
    return db.get(Finding, finding_id)


def get_finding_by_identity(
    db: Session,
    *,
    account_id: UUID,
    scanner_name: str,
    resource_id: str,
    resource_type: str,
    title: str,
) -> Finding | None:
    statement = select(Finding).where(
        Finding.account_id == account_id,
        Finding.scanner_name == scanner_name,
        Finding.resource_id == resource_id,
        Finding.resource_type == resource_type,
        Finding.title == title,
    )
    return db.execute(statement).scalar_one_or_none()


def update_finding(
    finding: Finding,
    *,
    scan_id: UUID | None,
    severity: FindingSeverity,
    status: FindingStatus,
    description: str,
    region: str | None,
    risk_score: Decimal | None,
    remediation: str | None,
    resource_metadata: dict[str, object] | None,
    seen_at: datetime,
) -> Finding:
    finding.scan_id = scan_id
    finding.severity = severity
    finding.status = status
    finding.description = description
    finding.region = region
    finding.risk_score = risk_score
    finding.remediation = remediation
    finding.resource_metadata = resource_metadata
    finding.last_seen_at = seen_at
    finding.occurrence_count = (finding.occurrence_count or 0) + 1
    return finding


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


def count_findings_for_scan(db: Session, scan_id: UUID) -> int:
    statement = select(func.count(Finding.id)).where(Finding.scan_id == scan_id)
    return int(db.execute(statement).scalar_one())


def count_findings_for_scan_by_severity(
    db: Session,
    scan_id: UUID,
) -> dict[FindingSeverity, int]:
    statement = (
        select(Finding.severity, func.count(Finding.id))
        .where(Finding.scan_id == scan_id)
        .group_by(Finding.severity)
    )
    return {severity: int(count) for severity, count in db.execute(statement).all()}


def count_findings_for_scan_by_status(
    db: Session,
    scan_id: UUID,
) -> dict[FindingStatus, int]:
    statement = (
        select(Finding.status, func.count(Finding.id))
        .where(Finding.scan_id == scan_id)
        .group_by(Finding.status)
    )
    return {status: int(count) for status, count in db.execute(statement).all()}
