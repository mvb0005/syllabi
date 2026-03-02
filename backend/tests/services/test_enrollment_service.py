"""Tests for EnrollmentService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions import ConflictError, NotFoundError
from backend.models.course import Course
from backend.models.user import User, UserRole
from backend.services.enrollment_service import EnrollmentService


async def _make_user(db: AsyncSession, *, role: UserRole = UserRole.student) -> User:
    """Persist a minimal User and return it."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@test.com",
        full_name="Test",
        hashed_password="hashed",
        role=role,
    )
    db.add(user)
    await db.flush()
    return user


async def _make_course(db: AsyncSession, instructor_id: str) -> Course:
    """Persist a minimal Course and return it."""
    course = Course(
        id=str(uuid.uuid4()),
        title="Test Course",
        instructor_id=instructor_id,
    )
    db.add(course)
    await db.flush()
    return course


@pytest.mark.asyncio
async def test_enroll_student_success(db_session: AsyncSession) -> None:
    """EnrollmentService.enroll_student creates and returns an Enrollment."""
    instructor = await _make_user(db_session, role=UserRole.instructor)
    student = await _make_user(db_session)
    course = await _make_course(db_session, instructor.id)

    svc = EnrollmentService(db_session)
    enrollment = await svc.enroll_student(course.id, student.id)

    assert enrollment.id is not None
    assert enrollment.student_id == student.id
    assert enrollment.course_id == course.id
    assert enrollment.enrolled_at is not None


@pytest.mark.asyncio
async def test_enroll_student_duplicate_raises_conflict(db_session: AsyncSession) -> None:
    """Enrolling the same student twice raises ConflictError."""
    instructor = await _make_user(db_session, role=UserRole.instructor)
    student = await _make_user(db_session)
    course = await _make_course(db_session, instructor.id)

    svc = EnrollmentService(db_session)
    await svc.enroll_student(course.id, student.id)
    with pytest.raises(ConflictError):
        await svc.enroll_student(course.id, student.id)


@pytest.mark.asyncio
async def test_enroll_student_course_not_found(db_session: AsyncSession) -> None:
    """Enrolling in a non-existent course raises NotFoundError."""
    student = await _make_user(db_session)
    svc = EnrollmentService(db_session)
    with pytest.raises(NotFoundError):
        await svc.enroll_student("non-existent-course", student.id)


@pytest.mark.asyncio
async def test_is_enrolled_true(db_session: AsyncSession) -> None:
    """is_enrolled returns True after enrollment."""
    instructor = await _make_user(db_session, role=UserRole.instructor)
    student = await _make_user(db_session)
    course = await _make_course(db_session, instructor.id)

    svc = EnrollmentService(db_session)
    await svc.enroll_student(course.id, student.id)
    assert await svc.is_enrolled(course.id, student.id) is True


@pytest.mark.asyncio
async def test_is_enrolled_false(db_session: AsyncSession) -> None:
    """is_enrolled returns False when no enrollment exists."""
    instructor = await _make_user(db_session, role=UserRole.instructor)
    student = await _make_user(db_session)
    course = await _make_course(db_session, instructor.id)

    svc = EnrollmentService(db_session)
    assert await svc.is_enrolled(course.id, student.id) is False


@pytest.mark.asyncio
async def test_get_enrollments_for_course(db_session: AsyncSession) -> None:
    """get_enrollments_for_course returns all enrolled students."""
    instructor = await _make_user(db_session, role=UserRole.instructor)
    student_a = await _make_user(db_session)
    student_b = await _make_user(db_session)
    course = await _make_course(db_session, instructor.id)

    svc = EnrollmentService(db_session)
    await svc.enroll_student(course.id, student_a.id)
    await svc.enroll_student(course.id, student_b.id)

    enrollments = await svc.get_enrollments_for_course(course.id)
    student_ids = {e.student_id for e in enrollments}
    assert student_ids == {student_a.id, student_b.id}


@pytest.mark.asyncio
async def test_get_enrollments_empty_for_new_course(db_session: AsyncSession) -> None:
    """get_enrollments_for_course returns empty list for unenrolled course."""
    instructor = await _make_user(db_session, role=UserRole.instructor)
    course = await _make_course(db_session, instructor.id)

    svc = EnrollmentService(db_session)
    assert await svc.get_enrollments_for_course(course.id) == []
