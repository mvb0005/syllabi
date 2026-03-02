"""FastAPI dependency providers."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models.user import User


async def get_db_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """Re-export get_db under a descriptive name for use in routers."""
    yield session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT access_token cookie and return the authenticated User.

    Args:
        request: The incoming HTTP request (used to read cookies).
        db: Async database session.

    Returns:
        The authenticated User ORM instance.

    Raises:
        HTTPException: 401 if the cookie is missing, the token is invalid,
            or the user no longer exists.
    """
    token: str | None = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise JWTError("missing sub")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def instructor_required(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the authenticated user has the instructor role.

    Args:
        current_user: Injected by get_current_user.

    Returns:
        The current user if they are an instructor.

    Raises:
        HTTPException: 403 if the user is not an instructor.
    """
    if str(current_user.role) != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required",
        )
    return current_user


async def student_required(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the authenticated user has the student role.

    Args:
        current_user: Injected by get_current_user.

    Returns:
        The current user if they are a student.

    Raises:
        HTTPException: 403 if the user is not a student.
    """
    if str(current_user.role) != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user


__all__ = [
    "User",
    "get_current_user",
    "get_db",
    "get_db_session",
    "instructor_required",
    "student_required",
]
