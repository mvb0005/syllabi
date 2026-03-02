"""Submission and GradeRecord ORM models."""

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, new_uuid


class SubmissionStatus(enum.StrEnum):
    """Lifecycle state of a student submission."""

    pending = "pending"
    grading = "grading"
    graded = "graded"
    error = "error"


class GradedBy(enum.StrEnum):
    """How a grade record was produced."""

    deterministic = "deterministic"
    llm = "llm"
    instructor_override = "instructor_override"


class Submission(Base, TimestampMixin):
    """A single student submission for an assignment."""

    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    assignment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submissionstatus"),
        nullable=False,
        default=SubmissionStatus.pending,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class GradeRecord(Base):
    """The grade produced for a submission.

    ``private_reasoning`` is NEVER returned to students — use ``GradeRecordPublic``
    schema which omits it.
    """

    __tablename__ = "grade_records"
    __table_args__ = (UniqueConstraint("submission_id", name="uq_grade_submission"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    public_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    private_reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    graded_by: Mapped[GradedBy] = mapped_column(
        Enum(GradedBy, name="gradedby"),
        nullable=False,
        default=GradedBy.deterministic,
    )
    graded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
