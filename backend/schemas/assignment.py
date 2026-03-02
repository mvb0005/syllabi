"""Pydantic schemas for Assignment and TestCase resources."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.assignment import GradingType


class AssignmentBase(BaseModel):
    """Shared fields for assignment schemas."""

    title: str
    description_md: str = ""
    grading_type: GradingType = GradingType.deterministic
    max_score: int = 100
    due_at: datetime | None = None


class AssignmentCreate(AssignmentBase):
    """Request body for creating an assignment."""


class AssignmentUpdate(BaseModel):
    """Request body for updating an assignment."""

    title: str | None = None
    description_md: str | None = None
    grading_type: GradingType | None = None
    max_score: int | None = None
    due_at: datetime | None = None


class AssignmentPublic(AssignmentBase):
    """Assignment representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    module_id: str


# ---------------------------------------------------------------------------
# TestCase schemas — code field is OPAQUE, never returned to students
# ---------------------------------------------------------------------------


class TestCaseCreate(BaseModel):
    """Request body for creating a test case (instructor only)."""

    name: str
    code: str
    weight: float = 1.0
    is_hidden: bool = True


class TestCasePublic(BaseModel):
    """Test case fields visible to students — code is deliberately omitted."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    assignment_id: str
    name: str
    weight: float
    is_hidden: bool


class TestCaseFull(TestCasePublic):
    """Full test case including code — for instructor/admin use only."""

    code: str
