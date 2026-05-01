from decimal import Decimal

import pytest

from app.models.finding import FindingSeverity
from app.services.risk import calculate_finding_risk_score, normalize_risk_score


@pytest.mark.parametrize(
    ("severity", "expected_score"),
    (
        (FindingSeverity.CRITICAL, Decimal("9.50")),
        (FindingSeverity.HIGH, Decimal("7.50")),
        (FindingSeverity.MEDIUM, Decimal("5.00")),
        (FindingSeverity.LOW, Decimal("2.50")),
        (FindingSeverity.INFO, Decimal("0.50")),
    ),
)
def test_calculate_finding_risk_score_uses_severity_baseline(
    severity: FindingSeverity,
    expected_score: Decimal,
):
    assert calculate_finding_risk_score(severity=severity) == expected_score


def test_calculate_finding_risk_score_increases_public_admin_exposure():
    score = calculate_finding_risk_score(
        severity=FindingSeverity.CRITICAL,
        metadata={
            "source": "0.0.0.0/0",
            "exposes_admin_port": True,
        },
    )

    assert score == Decimal("10.00")


def test_calculate_finding_risk_score_increases_effective_public_s3_acl():
    score = calculate_finding_risk_score(
        severity=FindingSeverity.HIGH,
        metadata={
            "detection_source": "bucket_acl",
            "blocks_all_public_access": False,
        },
    )

    assert score == Decimal("7.75")


def test_calculate_finding_risk_score_increases_console_user_without_mfa():
    score = calculate_finding_risk_score(
        severity=FindingSeverity.HIGH,
        metadata={
            "password_enabled": True,
            "mfa_device_count": 0,
        },
    )

    assert score == Decimal("7.75")


def test_normalize_risk_score_quantizes_and_clamps():
    assert normalize_risk_score(Decimal("7.135")) == Decimal("7.14")
    assert normalize_risk_score(Decimal("-1.00")) == Decimal("0.00")
    assert normalize_risk_score(Decimal("12.25")) == Decimal("10.00")
