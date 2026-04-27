from app.models import (
    Account,
    AccountStatus,
    CloudProvider,
    Finding,
    FindingSeverity,
    FindingStatus,
    Scan,
    ScanStatus,
)


def test_expected_table_names():
    assert Account.__tablename__ == "accounts"
    assert Scan.__tablename__ == "scans"
    assert Finding.__tablename__ == "findings"


def test_account_unique_constraint_covers_provider_and_external_id():
    constraint_names = {
        constraint.name
        for constraint in Account.__table__.constraints
        if getattr(constraint, "name", None)
    }

    assert "uq_accounts_provider_external_id" in constraint_names


def test_relationship_foreign_keys_exist():
    assert Scan.__table__.c.account_id.foreign_keys
    assert Finding.__table__.c.account_id.foreign_keys
    assert Finding.__table__.c.scan_id.foreign_keys


def test_default_enum_values_are_defined():
    assert AccountStatus.PENDING.value == "pending"
    assert ScanStatus.QUEUED.value == "queued"
    assert FindingStatus.OPEN.value == "open"
    assert FindingSeverity.CRITICAL.value == "critical"
    assert CloudProvider.AWS.value == "aws"


def test_sqlalchemy_enums_use_database_values():
    assert Account.__table__.c.cloud_provider.type.enums == ["aws", "azure", "gcp"]
    assert Account.__table__.c.status.type.enums == [
        "pending",
        "active",
        "disconnected",
    ]
    assert Scan.__table__.c.status.type.enums == [
        "queued",
        "running",
        "completed",
        "failed",
    ]
    assert Finding.__table__.c.severity.type.enums == [
        "critical",
        "high",
        "medium",
        "low",
        "info",
    ]
    assert Finding.__table__.c.status.type.enums == ["open", "triaged", "resolved"]
