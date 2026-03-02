"""Assignment and TestCase ORM models."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, new_uuid


class GradingType(enum.StrEnum):
    """Grading strategy for an assignment."""

    deterministic = "deterministic"
    llm_rubric = "llm_rubric"
    hybrid = "hybrid"


class Assignment(Base, TimestampMixin):
    """An assignment belonging to a module."""

    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    module_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    grading_type: Mapped[GradingType] = mapped_column(
        Enum(GradingType, name="gradingtype"),
        nullable=False,
        default=GradingType.deterministic,
    )
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="assignment", cascade="all, delete-orphan"
    )


class TestCase(Base):
    """A test case for deterministic grading.

    OPAQUE: The ``code`` field must NEVER be exposed to students via API.
    """

    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    assignment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="test_cases")
