"""add table for server theme presets

Revision ID: 7b1d4e9a2c58
Revises: c4d2e8a91b37
Create Date: 2026-10-17 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "7b1d4e9a2c58"
down_revision: str | None = "c4d2e8a91b37"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "server_theme_presets",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("colors", sa.JSON(), nullable=False),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("server_theme_presets", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_server_theme_presets_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_server_theme_presets_name"), ["name"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("server_theme_presets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_server_theme_presets_name"))
        batch_op.drop_index(batch_op.f("ix_server_theme_presets_created_at"))

    op.drop_table("server_theme_presets")
