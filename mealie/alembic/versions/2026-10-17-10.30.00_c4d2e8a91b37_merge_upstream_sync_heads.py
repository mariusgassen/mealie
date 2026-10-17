"""'merge upstream sync heads'

Revision ID: c4d2e8a91b37
Revises: 1e69ea7cd45e, a3f1c9d27b64
Create Date: 2026-10-17 10:30:00.000000

"""

from alembic import op  # noqa: F401

# revision identifiers, used by Alembic.
revision = "c4d2e8a91b37"
down_revision: str | tuple[str, ...] | None = ("1e69ea7cd45e", "a3f1c9d27b64")
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    pass


def downgrade():
    pass
