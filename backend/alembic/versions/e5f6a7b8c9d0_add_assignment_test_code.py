"""add assignments.test_code — fixed harness appended server-side

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema — add assignments.test_code."""
    op.add_column(
        "assignments",
        sa.Column("test_code", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    """Downgrade schema — drop assignments.test_code."""
    op.drop_column("assignments", "test_code")
