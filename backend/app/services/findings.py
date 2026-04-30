from collections.abc import Iterable, Mapping
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.repositories.findings import create_finding
from app.scanners import FindingDraft, ScannerRunResult


class FindingPersistenceError(Exception):
    pass


def persist_scanner_findings(
    db: Session,
    *,
    account_id: UUID,
    scanner_results: Iterable[ScannerRunResult],
    scan_id: UUID | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    for scanner_result in scanner_results:
        for draft in scanner_result.findings:
            findings.append(
                persist_finding_draft(
                    db,
                    account_id=account_id,
                    scanner_name=scanner_result.scanner_name,
                    draft=draft,
                    scan_id=scan_id,
                    commit=False,
                )
            )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FindingPersistenceError from exc

    for finding in findings:
        db.refresh(finding)
    return findings


def persist_finding_draft(
    db: Session,
    *,
    account_id: UUID,
    scanner_name: str,
    draft: FindingDraft,
    scan_id: UUID | None = None,
    commit: bool = True,
) -> Finding:
    finding = create_finding(
        db,
        account_id=account_id,
        scan_id=scan_id,
        scanner_name=scanner_name,
        severity=draft.severity,
        title=draft.title,
        description=draft.description,
        resource_id=draft.resource_id,
        resource_type=draft.resource_type,
        region=draft.region,
        risk_score=_normalize_risk_score(draft.risk_score),
        remediation=draft.remediation,
        resource_metadata=_normalize_metadata(draft.metadata),
    )

    if not commit:
        return finding

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FindingPersistenceError from exc

    db.refresh(finding)
    return finding


def _normalize_risk_score(risk_score: Decimal | None) -> Decimal | None:
    if risk_score is None:
        return None
    return risk_score.quantize(Decimal("0.01"))


def _normalize_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    return {key: _normalize_metadata_value(value) for key, value in dict(metadata).items()}


def _normalize_metadata_value(value: object) -> object:
    if isinstance(value, tuple):
        return [_normalize_metadata_value(item) for item in value]
    return value
