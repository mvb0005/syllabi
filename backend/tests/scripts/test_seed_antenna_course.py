"""Tests for the antenna-software-curriculum seed script."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.assignment import Assignment, GradingType, TestCase
from backend.models.course import Course, Module
from backend.models.user import User, UserRole
from backend.scripts.seed_antenna_course import (
    COURSE_TITLE,
    SEED_INSTRUCTOR_EMAIL,
    seed_antenna_course,
)


@pytest.mark.asyncio
async def test_seed_creates_course_with_six_modules(db_session: AsyncSession) -> None:
    """Seeding creates the course with one module per curriculum phase."""
    course = await seed_antenna_course(db_session)

    assert course.title == COURSE_TITLE
    assert course.is_published is True

    modules = (await db_session.scalars(select(Module).where(Module.course_id == course.id))).all()
    assert len(modules) == 6
    assert [m.order_index for m in sorted(modules, key=lambda m: m.order_index)] == list(range(6))
    assert modules[0].title.startswith("Phase I")


@pytest.mark.asyncio
async def test_seed_creates_seed_instructor(db_session: AsyncSession) -> None:
    """Seeding creates (or reuses) a dedicated instructor user for the course."""
    course = await seed_antenna_course(db_session)

    instructor = await db_session.get(User, course.instructor_id)
    assert instructor is not None
    assert instructor.email == SEED_INSTRUCTOR_EMAIL
    assert instructor.role == UserRole.instructor


@pytest.mark.asyncio
async def test_seed_creates_deterministic_assignments_with_test_cases(
    db_session: AsyncSession,
) -> None:
    """Each phase with starter code gets a deterministic assignment and self-test."""
    course = await seed_antenna_course(db_session)

    module_ids = (
        await db_session.scalars(select(Module.id).where(Module.course_id == course.id))
    ).all()
    assignments = (
        await db_session.scalars(select(Assignment).where(Assignment.module_id.in_(module_ids)))
    ).all()
    assert len(assignments) == 6  # one assignment per phase module

    deterministic_assignments = [
        a for a in assignments if a.grading_type == GradingType.deterministic
    ]
    assert len(deterministic_assignments) == 4  # phases I, II, III, V ship starter code

    for assignment in deterministic_assignments:
        test_case_count = await db_session.scalar(
            select(func.count())
            .select_from(TestCase)
            .where(TestCase.assignment_id == assignment.id)
        )
        assert test_case_count == 1


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session: AsyncSession) -> None:
    """Running the seed twice does not create a duplicate course or instructor."""
    first = await seed_antenna_course(db_session)
    second = await seed_antenna_course(db_session)

    assert first.id == second.id

    course_count = await db_session.scalar(
        select(func.count()).select_from(Course).where(Course.title == COURSE_TITLE)
    )
    assert course_count == 1

    instructor_count = await db_session.scalar(
        select(func.count()).select_from(User).where(User.email == SEED_INSTRUCTOR_EMAIL)
    )
    assert instructor_count == 1
