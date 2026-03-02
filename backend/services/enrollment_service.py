"""Enrollment service — business logic for student course enrollments."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions import ConflictError, NotFoundError
from backend.models.course import Course
from backend.models.enrollment import Enrollment


class EnrollmentService:
    """Handles enrollment database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with an async database session."""
        self._db = db

    async def enroll_student(self, course_id: str, student_id: str) -> Enrollment:
        """Enroll a student in a course.

        Args:
            course_id: Primary key of the course.
            student_id: Primary key of the student user.

        Returns:
            The newly created Enrollment ORM instance.

        Raises:
            NotFoundError: If the course does not exist.
            ConflictError: If the student is already enrolled.
        """
        if await self._db.get(Course, course_id) is None:
            raise NotFoundError("Course", course_id)
        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        self._db.add(enrollment)
        try:
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(
                f"Student {student_id} is already enrolled in course {course_id}."
            ) from exc
        await self._db.refresh(enrollment)
        return enrollment

    async def is_enrolled(self, course_id: str, student_id: str) -> bool:
        """Return True if the student is enrolled in the course.

        Args:
            course_id: Primary key of the course.
            student_id: Primary key of the student user.

        Returns:
            ``True`` if an active enrollment record exists, else ``False``.
        """
        result = await self._db.scalar(
            select(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.student_id == student_id,
            )
        )
        return result is not None

    async def get_enrollments_for_course(self, course_id: str) -> list[Enrollment]:
        """Return all enrollment records for a course.

        Args:
            course_id: Primary key of the course.

        Returns:
            List of Enrollment ORM instances (may be empty).
        """
        rows = await self._db.scalars(select(Enrollment).where(Enrollment.course_id == course_id))
        return list(rows)
