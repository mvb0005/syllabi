"""add enrollments table

Revision ID: a1b2c3d4e5f6
Revises: 0cdbd53739f9
Create Date: 2026-03-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "0cdbd53739f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema — create enrollments table."""
    op.create_table(
        "enrollments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_id", name="uq_enrollment"),
    )
    op.create_index(
        op.f("ix_enrollments_student_id"), "enrollments", ["student_id"], unique=False
    )
    op.create_index(
        op.f("ix_enrollments_course_id"), "enrollments", ["course_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema — drop enrollments table."""
    op.drop_index(op.f("ix_enrollments_course_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_student_id"), table_name="enrollments")
    op.drop_table("enrollments")
