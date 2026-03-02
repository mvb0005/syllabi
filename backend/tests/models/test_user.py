"""Tests for the User ORM model."""

from sqlite3 import IntegrityError

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """User can be created with required fields."""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.student,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == UserRole.student
    assert user.is_active is True


@pytest.mark.asyncio
async def test_user_default_role_is_student(db_session: AsyncSession) -> None:
    """User role defaults to student."""
    user = User(
        email="student@example.com",
        hashed_password="hashed",
        full_name="Student",
    )
    db_session.add(user)
    await db_session.commit()
    assert user.role == UserRole.student


@pytest.mark.asyncio
async def test_user_email_is_unique(db_session: AsyncSession) -> None:
    """Two users cannot share the same email."""
    u1 = User(email="dup@example.com", hashed_password="h", full_name="A")
    u2 = User(email="dup@example.com", hashed_password="h", full_name="B")
    db_session.add(u1)
    await db_session.commit()
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
