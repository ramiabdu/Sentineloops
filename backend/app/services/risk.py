from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType

from app.models.finding import FindingSeverity

MIN_RISK_SCORE = Decimal("0.00")
MAX_RISK_SCORE = Decimal("10.00")
RISK_SCORE_STEP = Decimal("0.01")

SEVERITY_BASE_SCORES = MappingProxyType(
    {
        FindingSeverity.CRITICAL: Decimal("9.50"),
        FindingSeverity.HIGH: Decimal("7.50"),
        FindingSeverity.MEDIUM: Decimal("5.00"),
        FindingSeverity.LOW: Decimal("2.50"),
        FindingSeverity.INFO: Decimal("0.50"),
    }
)

PUBLIC_INTERNET_SOURCES = frozenset({"0.0.0.0/0", "::/0"})
PUBLIC_S3_DETECTION_SOURCES = frozenset({"bucket_policy_status", "bucket_acl"})

PUBLIC_EXPOSURE_MODIFIER = Decimal("0.25")
ADMIN_EXPOSURE_MODIFIER = Decimal("0.50")
CONSOLE_PASSWORD_WITHOUT_MFA_MODIFIER = Decimal("0.25")


def calculate_finding_risk_score(
    *,
    severity: FindingSeverity,
    metadata: Mapping[str, object] | None = None,
) -> Decimal:
    score = SEVERITY_BASE_SCORES[severity]
    context = metadata or {}

    if _is_publicly_exposed(context):
        score += PUBLIC_EXPOSURE_MODIFIER
    if context.get("exposes_admin_port") is True:
        score += ADMIN_EXPOSURE_MODIFIER
    if _is_console_user_without_mfa(context):
        score += CONSOLE_PASSWORD_WITHOUT_MFA_MODIFIER

    return normalize_risk_score(score)


def resolve_finding_risk_score(
    *,
    severity: FindingSeverity,
    explicit_risk_score: Decimal | None,
    metadata: Mapping[str, object] | None = None,
) -> Decimal:
    if explicit_risk_score is not None:
        return normalize_risk_score(explicit_risk_score)
    return calculate_finding_risk_score(severity=severity, metadata=metadata)


def normalize_risk_score(risk_score: Decimal) -> Decimal:
    bounded_score = max(MIN_RISK_SCORE, min(MAX_RISK_SCORE, risk_score))
    return bounded_score.quantize(RISK_SCORE_STEP)


def _is_publicly_exposed(metadata: Mapping[str, object]) -> bool:
    if metadata.get("source") in PUBLIC_INTERNET_SOURCES:
        return True
    return (
        metadata.get("detection_source") in PUBLIC_S3_DETECTION_SOURCES
        and metadata.get("blocks_all_public_access") is False
    )


def _is_console_user_without_mfa(metadata: Mapping[str, object]) -> bool:
    return metadata.get("password_enabled") is True and metadata.get("mfa_device_count") == 0
