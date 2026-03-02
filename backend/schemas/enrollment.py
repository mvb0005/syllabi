"""Pydantic schemas for Enrollment resources."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentCreate(BaseModel):
    """Request body for enrolling a student in a course.

    ``student_id`` may be omitted by a student (self-enroll) or supplied by
    an instructor to enroll another student.
    """

    student_id: str | None = None


class EnrollmentPublic(BaseModel):
    """Enrollment representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    course_id: str
    enrolled_at: datetime
