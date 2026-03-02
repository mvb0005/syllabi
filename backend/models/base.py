"""Base SQLAlchemy declarative class and shared mixins."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class TimestampMixin:
    """Mixin that adds created_at / updated_at columns to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


def new_uuid() -> str:
    """Generate a new UUID4 string primary key."""
    return str(uuid.uuid4())


__all__ = ["Base", "String", "TimestampMixin", "new_uuid"]
