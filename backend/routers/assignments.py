"""Assignments router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.exceptions import NotFoundError
from backend.schemas.assignment import AssignmentCreate, AssignmentPublic, AssignmentUpdate
from backend.services.course_service import CourseService

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/", response_model=AssignmentPublic, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    module_id: str,
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
) -> AssignmentPublic:
    """Create an assignment for a module."""
    try:
        assignment = await CourseService(db).create_assignment(module_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AssignmentPublic.model_validate(assignment)


@router.get("/{assignment_id}", response_model=AssignmentPublic)
async def get_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
) -> AssignmentPublic:
    """Retrieve an assignment by ID."""
    try:
        assignment = await CourseService(db).get_assignment(assignment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AssignmentPublic.model_validate(assignment)


@router.patch("/{assignment_id}", response_model=AssignmentPublic)
async def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> AssignmentPublic:
    """Update an assignment."""
    try:
        assignment = await CourseService(db).update_assignment(assignment_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AssignmentPublic.model_validate(assignment)
