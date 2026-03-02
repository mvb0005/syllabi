"""Pydantic schemas for Submission and GradeRecord resources."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.submission import GradedBy, SubmissionStatus


class SubmissionCreate(BaseModel):
    """Request body for creating a submission."""

    assignment_id: str
    content: str


class SubmissionPublic(BaseModel):
    """Submission representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    assignment_id: str
    student_id: str
    status: SubmissionStatus
    submitted_at: datetime


# ---------------------------------------------------------------------------
# GradeRecord schemas
# private_reasoning is NEVER included in API responses — server-side only.
# ---------------------------------------------------------------------------


class GradeRecordPublic(BaseModel):
    """Grade record safe for student-facing API responses.

    ``private_reasoning`` is intentionally omitted from this schema.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    raw_score: float
    max_score: float
    percentage: float
    public_feedback: str
    graded_by: GradedBy
    graded_at: datetime
