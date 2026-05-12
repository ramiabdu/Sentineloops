from alembic import op

# revision identifiers, used by Alembic.
revision = "20260512_0002"
down_revision = "20260424_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM findings
        WHERE id IN (
            SELECT id
            FROM (
                SELECT
                    id,
                    row_number() OVER (
                        PARTITION BY
                            account_id,
                            scanner_name,
                            resource_id,
                            resource_type,
                            title
                        ORDER BY updated_at DESC, created_at DESC, id DESC
                    ) AS duplicate_rank
                FROM findings
            ) duplicate_findings
            WHERE duplicate_rank > 1
        )
        """
    )
    op.create_unique_constraint(
        "uq_findings_dedup_identity",
        "findings",
        ["account_id", "scanner_name", "resource_id", "resource_type", "title"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_findings_dedup_identity",
        "findings",
        type_="unique",
    )
