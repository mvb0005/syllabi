"""Users router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.exceptions import ConflictError, NotFoundError
from backend.schemas.user import UserCreate, UserPublic, UserUpdate
from backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """Register a new user account."""
    try:
        user = await UserService(db).create_user(payload)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserPublic.model_validate(user)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """Retrieve a user by ID."""
    try:
        user = await UserService(db).get_user(user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return UserPublic.model_validate(user)


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """Update an existing user."""
    try:
        user = await UserService(db).update_user(user_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return UserPublic.model_validate(user)
