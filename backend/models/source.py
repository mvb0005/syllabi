"""Source and SourceExcerpt ORM models.

A Source is a third-party reference work (textbook PDF, plain-text notes)
stored under the repository's ``sources/`` directory. A SourceExcerpt embeds
a specific page range of a source into a course module, always rendered with
a full citation. The extracted text is cached on the excerpt at creation
time so serving a course page never re-opens the source file.
"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, new_uuid


class SourceKind(enum.StrEnum):
    """Supported source file formats."""

    pdf = "pdf"
    text = "text"


class Source(Base, TimestampMixin):
    """A third-party reference work that excerpts can cite."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    bibkey: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[str] = mapped_column(String(500), nullable=False)
    edition: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    publisher: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    kind: Mapped[SourceKind] = mapped_column(
        Enum(SourceKind, name="sourcekind"), nullable=False, default=SourceKind.pdf
    )
    # Path relative to the sources/ directory; never absolute.
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    # Printed page number = PDF page number - page_offset (front matter
    # shifts a book's own numbering); citations render printed numbers.
    page_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    excerpts: Mapped[list["SourceExcerpt"]] = relationship(
        "SourceExcerpt", back_populates="source", cascade="all, delete-orphan"
    )


class SourceExcerpt(Base, TimestampMixin):
    """A cited page range of a source embedded in a course module."""

    __tablename__ = "source_excerpts"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "module_id", "page_start", "page_end", name="uq_excerpt_span"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    context_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Text extracted from the source's page range at creation time.
    content_text: Mapped[str] = mapped_column(Text, nullable=False)

    source: Mapped[Source] = relationship("Source", back_populates="excerpts")
