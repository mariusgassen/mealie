"""add table for server theme overrides

Revision ID: a3f1c9d27b64
Revises: 5e62206b4547
Create Date: 2026-10-09 08:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "a3f1c9d27b64"
down_revision: str | None = "5e62206b4547"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "server_theme_overrides",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("server_theme_overrides", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_server_theme_overrides_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_server_theme_overrides_key"), ["key"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("server_theme_overrides", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_server_theme_overrides_key"))
        batch_op.drop_index(batch_op.f("ix_server_theme_overrides_created_at"))

    op.drop_table("server_theme_overrides")
