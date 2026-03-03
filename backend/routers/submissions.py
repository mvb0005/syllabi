"""Submissions router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user, student_required
from backend.exceptions import NotFoundError
from backend.models.assignment import Assignment
from backend.models.course import Module
from backend.models.submission import Submission
from backend.models.user import User, UserRole
from backend.schemas.submission import GradeRecordPublic, SubmissionCreate, SubmissionPublic
from backend.services.enrollment_service import EnrollmentService
from backend.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=SubmissionPublic, status_code=status.HTTP_201_CREATED)
async def create_submission(
    payload: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(student_required),
) -> SubmissionPublic:
    """Submit work for an assignment.

    The student must be enrolled in the assignment's course.
    ``student_id`` is derived from the authenticated user's JWT token.
    """
    assignment = await db.get(Assignment, payload.assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment '{payload.assignment_id}' not found",
        )
    module = await db.get(Module, assignment.module_id)
    if module is None:  # pragma: no cover — referential integrity guarantees this
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    enrolled = await EnrollmentService(db).is_enrolled(module.course_id, current_user.id)
    if not enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course.",
        )
    try:
        submission = await SubmissionService(db).create_submission(
            payload, student_id=current_user.id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SubmissionPublic.model_validate(submission)


@router.get("/{submission_id}", response_model=SubmissionPublic)
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
) -> SubmissionPublic:
    """Retrieve a submission by ID."""
    try:
        submission = await SubmissionService(db).get_submission(submission_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SubmissionPublic.model_validate(submission)


@router.get("/{submission_id}/grade", response_model=GradeRecordPublic)
async def get_grade(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GradeRecordPublic:
    """Retrieve the grade for a submission.

    Only the submitting student or any instructor may view a grade.
    Only ``public_feedback`` is returned — ``private_reasoning`` is never exposed.
    """
    submission = await db.scalar(select(Submission).where(Submission.id == submission_id))
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{submission_id}' not found",
        )
    if current_user.role != UserRole.instructor and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this grade.",
        )
    try:
        grade = await SubmissionService(db).get_grade(submission_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GradeRecordPublic.model_validate(grade)
