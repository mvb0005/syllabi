"""Course and Module ORM models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from backend.models.enrollment import Enrollment


class Course(Base, TimestampMixin):
    """A course created and owned by an instructor."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    instructor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    modules: Mapped[list[Module]] = relationship(
        "Module", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list[Enrollment]] = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )


class Module(Base, TimestampMixin):
    """A learning module belonging to a course."""

    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")

    course: Mapped[Course] = relationship("Course", back_populates="modules")
