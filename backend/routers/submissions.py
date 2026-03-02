"""Submissions router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.exceptions import NotFoundError
from backend.schemas.submission import GradeRecordPublic, SubmissionCreate, SubmissionPublic
from backend.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=SubmissionPublic, status_code=status.HTTP_201_CREATED)
async def create_submission(
    student_id: str,
    payload: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubmissionPublic:
    """Submit work for an assignment."""
    submission = await SubmissionService(db).create_submission(payload, student_id=student_id)
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
) -> GradeRecordPublic:
    """Retrieve the grade for a submission.

    Only ``public_feedback`` is returned — ``private_reasoning`` is never exposed.
    """
    try:
        grade = await SubmissionService(db).get_grade(submission_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GradeRecordPublic.model_validate(grade)
