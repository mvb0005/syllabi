"""Authentication router — login, logout, and current-user endpoints."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.user import LoginRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_access_token(user: User) -> str:
    """Encode a signed JWT for the given user.

    Args:
        user: The authenticated User ORM instance.

    Returns:
        A signed JWT string.
    """
    expire = datetime.now(tz=UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user.id,
        "role": str(user.role),
        "exp": int(expire.timestamp()),
    }
    return str(jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM))


@router.post("/login", response_model=UserPublic)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """Authenticate a user and issue a JWT in an httpOnly cookie.

    Args:
        payload: Login credentials (email + password).
        response: FastAPI response object used to set the cookie.
        db: Async database session.

    Returns:
        The authenticated user's public profile.

    Raises:
        HTTPException: 401 if the email is not found or password is wrong.
    """
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not _pwd_ctx.verify(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = _create_access_token(user)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True in production behind HTTPS
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return UserPublic.model_validate(user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict[str, str]:
    """Clear the access_token cookie to log out the user.

    Args:
        response: FastAPI response object used to delete the cookie.

    Returns:
        A confirmation message dict.
    """
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "logged out"}


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    """Return the public profile of the currently authenticated user.

    Args:
        current_user: Injected by the get_current_user dependency.

    Returns:
        The authenticated user's public profile.
    """
    return UserPublic.model_validate(current_user)
