"""Pydantic schemas for Course and Module resources."""

from pydantic import BaseModel, ConfigDict


class CourseBase(BaseModel):
    """Shared fields for course schemas."""

    title: str
    description: str = ""


class CourseCreate(CourseBase):
    """Request body for creating a course."""


class CourseUpdate(BaseModel):
    """Request body for updating a course."""

    title: str | None = None
    description: str | None = None
    is_published: bool | None = None


class CoursePublic(CourseBase):
    """Course representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    instructor_id: str
    is_published: bool


class ModuleBase(BaseModel):
    """Shared fields for module schemas."""

    title: str
    order_index: int = 0
    content_md: str = ""


class ModuleCreate(ModuleBase):
    """Request body for creating a module."""


class ModuleUpdate(BaseModel):
    """Request body for updating a module."""

    title: str | None = None
    order_index: int | None = None
    content_md: str | None = None


class ModulePublic(ModuleBase):
    """Module representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
