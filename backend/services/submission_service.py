"""Submission service — business logic for submissions and grades."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions import NotFoundError
from backend.models.submission import GradeRecord, Submission
from backend.schemas.submission import SubmissionCreate


class SubmissionService:
    """Handles submission and grade record database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with an async database session."""
        self._db = db

    async def create_submission(self, payload: SubmissionCreate, *, student_id: str) -> Submission:
        """Persist a new student submission.

        Args:
            payload: Validated submission data.
            student_id: ID of the submitting student.

        Returns:
            The newly created Submission ORM instance.
        """
        submission = Submission(
            assignment_id=payload.assignment_id,
            student_id=student_id,
            content=payload.content,
        )
        self._db.add(submission)
        await self._db.commit()
        await self._db.refresh(submission)
        return submission

    async def get_submission(self, submission_id: str) -> Submission:
        """Retrieve a submission by primary key.

        Raises:
            NotFoundError: If no submission with that ID exists.
        """
        submission = await self._db.get(Submission, submission_id)
        if submission is None:
            raise NotFoundError("Submission", submission_id)
        return submission

    async def get_grade(self, submission_id: str) -> GradeRecord:
        """Retrieve the grade record for a submission.

        Returns the full ``GradeRecord`` ORM object, including
        ``private_reasoning``. Callers MUST serialise through
        ``GradeRecordPublic`` (which omits ``private_reasoning``) before
        returning data to the client — never expose the raw ORM object
        directly in an API response.

        Raises:
            NotFoundError: If no grade record exists for the submission.
        """
        grade = await self._db.scalar(
            select(GradeRecord).where(GradeRecord.submission_id == submission_id)
        )
        if grade is None:
            raise NotFoundError("GradeRecord", submission_id)
        return grade
