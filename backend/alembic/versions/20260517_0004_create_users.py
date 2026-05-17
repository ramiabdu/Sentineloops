from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260517_0004"
down_revision = "20260513_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_exists = inspector.has_table("users")

    if not table_exists:
        op.create_table(
            "users",
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("display_name", sa.String(length=120), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    index_names = {
        index["name"]
        for index in sa.inspect(bind).get_indexes("users")
    }
    if "ix_users_email" not in index_names:
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    if "ix_users_role" not in index_names:
        op.create_index("ix_users_role", "users", ["role"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    index_names = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_role" in index_names:
        op.drop_index("ix_users_role", table_name="users")
    if "ix_users_email" in index_names:
        op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
