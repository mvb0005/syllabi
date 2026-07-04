"""add sources and source_excerpts tables

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-04 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema — create sources and source_excerpts tables."""
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("bibkey", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("authors", sa.String(length=500), nullable=False),
        sa.Column("edition", sa.String(length=100), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("kind", sa.Enum("pdf", "text", name="sourcekind"), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sources_bibkey"), "sources", ["bibkey"], unique=True)

    op.create_table(
        "source_excerpts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("module_id", sa.String(length=36), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("context_md", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id", "module_id", "page_start", "page_end", name="uq_excerpt_span"
        ),
    )
    op.create_index(
        op.f("ix_source_excerpts_source_id"), "source_excerpts", ["source_id"], unique=False
    )
    op.create_index(
        op.f("ix_source_excerpts_module_id"), "source_excerpts", ["module_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema — drop source_excerpts and sources tables."""
    op.drop_index(op.f("ix_source_excerpts_module_id"), table_name="source_excerpts")
    op.drop_index(op.f("ix_source_excerpts_source_id"), table_name="source_excerpts")
    op.drop_table("source_excerpts")
    op.drop_index(op.f("ix_sources_bibkey"), table_name="sources")
    op.drop_table("sources")
    sa.Enum(name="sourcekind").drop(op.get_bind(), checkfirst=True)
