"""add default_measurement_system

Revision ID: 42a93c909900
Revises: 27621d27c7e1
Create Date: 2026-09-27 14:35:39.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "42a93c909900"
down_revision: str | None = "27621d27c7e1"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("default_measurement_system", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.drop_column("default_measurement_system")
