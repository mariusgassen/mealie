"""add table for ai request logs

Revision ID: c4e7a1b9d3f2
Revises: 7b1d4e9a2c58
Create Date: 2026-10-18 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "c4e7a1b9d3f2"
down_revision: str | None = "7b1d4e9a2c58"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_request_logs",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("request_type", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("ai_request_logs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_ai_request_logs_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_request_logs_group_id"), ["group_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("ai_request_logs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_ai_request_logs_group_id"))
        batch_op.drop_index(batch_op.f("ix_ai_request_logs_created_at"))

    op.drop_table("ai_request_logs")
