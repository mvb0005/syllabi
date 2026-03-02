"""Courses router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user, instructor_required
from backend.exceptions import ConflictError, NotFoundError
from backend.models.user import User, UserRole
from backend.schemas.course import (
    CourseCreate,
    CoursePublic,
    CourseUpdate,
    ModuleCreate,
    ModulePublic,
)
from backend.schemas.enrollment import EnrollmentCreate, EnrollmentPublic
from backend.services.course_service import CourseService
from backend.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/", response_model=CoursePublic, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(instructor_required),
) -> CoursePublic:
    """Create a new course.

    The instructor_id is derived from the authenticated user's JWT token.

    Args:
        payload: Course creation data (title and description).
        db: Async database session.
        current_user: The authenticated instructor (injected by dependency).

    Returns:
        The newly created course.
    """
    try:
        course = await CourseService(db).create_course(payload, instructor_id=current_user.id)
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


@router.post(
    "/{course_id}/enroll",
    response_model=EnrollmentPublic,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    course_id: str,
    payload: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnrollmentPublic:
    """Enroll a student in a course.

    Students self-enroll (``student_id`` is taken from the JWT token).
    Instructors may supply a ``student_id`` to enroll another student.

    Args:
        course_id: The course to enroll in.
        payload: Optional ``student_id`` override (instructors only).
        db: Async database session.
        current_user: The authenticated user making the request.

    Returns:
        The created enrollment record.
    """
    if current_user.role == UserRole.instructor and payload.student_id is not None:
        target_student_id = payload.student_id
    else:
        target_student_id = current_user.id
    try:
        enrollment = await EnrollmentService(db).enroll_student(course_id, target_student_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail) from exc
    return EnrollmentPublic.model_validate(enrollment)
