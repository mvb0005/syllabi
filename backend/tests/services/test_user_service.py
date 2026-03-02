"""Tests for UserService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions import ConflictError, NotFoundError
from backend.schemas.user import UserCreate, UserUpdate
from backend.services.user_service import UserService


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """UserService.create_user persists and returns the new user."""
    svc = UserService(db_session)
    user = await svc.create_user(
        UserCreate(email="svc@test.com", full_name="SVC", password="secret")
    )
    assert user.id is not None
    assert user.email == "svc@test.com"
    assert user.hashed_password != "secret"


@pytest.mark.asyncio
async def test_create_user_duplicate_raises_conflict(db_session: AsyncSession) -> None:
    """Creating a duplicate email raises ConflictError."""
    svc = UserService(db_session)
    payload = UserCreate(email="dup@test.com", full_name="Dup", password="pw")
    await svc.create_user(payload)
    with pytest.raises(ConflictError):
        await svc.create_user(payload)


@pytest.mark.asyncio
async def test_get_user_not_found(db_session: AsyncSession) -> None:
    """Fetching a non-existent user raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await UserService(db_session).get_user("ghost-id")


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession) -> None:
    """UserService.update_user applies partial updates."""
    svc = UserService(db_session)
    user = await svc.create_user(
        UserCreate(email="update@test.com", full_name="Before", password="pw")
    )
    updated = await svc.update_user(user.id, UserUpdate(full_name="After"))
    assert updated.full_name == "After"


@pytest.mark.asyncio
async def test_verify_password(db_session: AsyncSession) -> None:
    """verify_password returns True for correct password."""
    svc = UserService(db_session)
    user = await svc.create_user(
        UserCreate(email="verify@test.com", full_name="V", password="correct")
    )
    assert svc.verify_password("correct", user.hashed_password) is True
    assert svc.verify_password("wrong", user.hashed_password) is False
