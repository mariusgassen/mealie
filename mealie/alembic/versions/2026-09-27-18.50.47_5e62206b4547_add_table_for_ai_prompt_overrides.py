"""add table for ai prompt overrides

Revision ID: 5e62206b4547
Revises: 42a93c909900
Create Date: 2026-09-27 18:50:47.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "5e62206b4547"
down_revision: str | None = "42a93c909900"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_prompt_overrides",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "name", name="ai_prompt_overrides_group_id_name_key"),
    )
    with op.batch_alter_table("ai_prompt_overrides", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_ai_prompt_overrides_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_prompt_overrides_group_id"), ["group_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_prompt_overrides_name"), ["name"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("ai_prompt_overrides", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_ai_prompt_overrides_name"))
        batch_op.drop_index(batch_op.f("ix_ai_prompt_overrides_group_id"))
        batch_op.drop_index(batch_op.f("ix_ai_prompt_overrides_created_at"))

    op.drop_table("ai_prompt_overrides")
