"""Courses router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.exceptions import NotFoundError
from backend.schemas.course import (
    CourseCreate,
    CoursePublic,
    CourseUpdate,
    ModuleCreate,
    ModulePublic,
)
from backend.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/", response_model=CoursePublic, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
) -> CoursePublic:
    """Create a new course.

    ``instructor_id`` is taken from the request body until Phase 3 replaces it
    with ``get_current_user``.
    """
    # TODO(phase3): replace payload.instructor_id with current_user.id
    try:
        course = await CourseService(db).create_course(payload, instructor_id=payload.instructor_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CoursePublic.model_validate(course)


@router.get("/{course_id}", response_model=CoursePublic)
async def get_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> CoursePublic:
    """Retrieve a course by ID."""
    try:
        course = await CourseService(db).get_course(course_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CoursePublic.model_validate(course)


@router.patch("/{course_id}", response_model=CoursePublic)
async def update_course(
    course_id: str,
    payload: CourseUpdate,
    db: AsyncSession = Depends(get_db),
) -> CoursePublic:
    """Update a course."""
    try:
        course = await CourseService(db).update_course(course_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CoursePublic.model_validate(course)


@router.post(
    "/{course_id}/modules",
    response_model=ModulePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_module(
    course_id: str,
    payload: ModuleCreate,
    db: AsyncSession = Depends(get_db),
) -> ModulePublic:
    """Add a module to a course."""
    try:
        module = await CourseService(db).create_module(course_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ModulePublic.model_validate(module)
