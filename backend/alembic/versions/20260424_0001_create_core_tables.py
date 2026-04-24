from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260424_0001"
down_revision = None
branch_labels = None
depends_on = None


cloud_provider = sa.Enum("aws", "azure", "gcp", name="cloud_provider")
account_status = sa.Enum("pending", "active", "disconnected", name="account_status")
scan_status = sa.Enum("queued", "running", "completed", "failed", name="scan_status")
finding_severity = sa.Enum(
    "critical",
    "high",
    "medium",
    "low",
    "info",
    name="finding_severity",
)
finding_status = sa.Enum("open", "triaged", "resolved", name="finding_status")


def upgrade() -> None:
    bind = op.get_bind()
    cloud_provider.create(bind, checkfirst=True)
    account_status.create(bind, checkfirst=True)
    scan_status.create(bind, checkfirst=True)
    finding_severity.create(bind, checkfirst=True)
    finding_status.create(bind, checkfirst=True)

    op.create_table(
        "accounts",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("cloud_provider", cloud_provider, nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("status", account_status, nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cloud_provider",
            "external_id",
            name="uq_accounts_provider_external_id",
        ),
    )
    op.create_index("ix_accounts_cloud_provider", "accounts", ["cloud_provider"], unique=False)
    op.create_index("ix_accounts_status", "accounts", ["status"], unique=False)

    op.create_table(
        "scans",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("status", scan_status, nullable=False),
        sa.Column("triggered_by", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scans_account_id", "scans", ["account_id"], unique=False)
    op.create_index("ix_scans_status", "scans", ["status"], unique=False)

    op.create_table(
        "findings",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=True),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("status", finding_status, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=True),
        sa.Column("scanner_name", sa.String(length=100), nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("resource_metadata", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_findings_account_id", "findings", ["account_id"], unique=False)
    op.create_index("ix_findings_scan_id", "findings", ["scan_id"], unique=False)
    op.create_index("ix_findings_scanner_name", "findings", ["scanner_name"], unique=False)
    op.create_index("ix_findings_severity", "findings", ["severity"], unique=False)
    op.create_index("ix_findings_status", "findings", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_findings_status", table_name="findings")
    op.drop_index("ix_findings_severity", table_name="findings")
    op.drop_index("ix_findings_scanner_name", table_name="findings")
    op.drop_index("ix_findings_scan_id", table_name="findings")
    op.drop_index("ix_findings_account_id", table_name="findings")
    op.drop_table("findings")

    op.drop_index("ix_scans_status", table_name="scans")
    op.drop_index("ix_scans_account_id", table_name="scans")
    op.drop_table("scans")

    op.drop_index("ix_accounts_status", table_name="accounts")
    op.drop_index("ix_accounts_cloud_provider", table_name="accounts")
    op.drop_table("accounts")

    bind = op.get_bind()
    finding_status.drop(bind, checkfirst=True)
    finding_severity.drop(bind, checkfirst=True)
    scan_status.drop(bind, checkfirst=True)
    account_status.drop(bind, checkfirst=True)
    cloud_provider.drop(bind, checkfirst=True)
