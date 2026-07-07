"""add assignments.starter_code for in-browser code milestones

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
Create Date: 2026-07-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema — add assignments.starter_code."""
    op.add_column(
        "assignments",
        sa.Column("starter_code", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    """Downgrade schema — drop assignments.starter_code."""
    op.drop_column("assignments", "starter_code")
