from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260513_0003"
down_revision = "20260512_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "findings",
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "findings",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "findings",
        sa.Column("occurrence_count", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE findings
        SET
            first_seen_at = created_at,
            last_seen_at = updated_at,
            occurrence_count = 1
        WHERE
            first_seen_at IS NULL
            OR last_seen_at IS NULL
            OR occurrence_count IS NULL
        """
    )
    op.alter_column("findings", "first_seen_at", nullable=False)
    op.alter_column("findings", "last_seen_at", nullable=False)
    op.alter_column("findings", "occurrence_count", nullable=False)


def downgrade() -> None:
    op.drop_column("findings", "occurrence_count")
    op.drop_column("findings", "last_seen_at")
    op.drop_column("findings", "first_seen_at")
