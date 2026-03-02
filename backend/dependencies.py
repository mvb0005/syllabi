"""FastAPI dependency providers."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User


async def get_db_session(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """Re-export get_db under a descriptive name for use in routers."""
    yield session


# ---------------------------------------------------------------------------
# Auth placeholder — will be replaced with JWT cookie validation in Phase 3
# ---------------------------------------------------------------------------


async def get_current_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the authenticated user from the request context.

    Raises:
        NotImplementedError: Auth is implemented in Phase 3.
    """
    raise NotImplementedError("JWT authentication is implemented in Phase 3")


__all__ = ["User", "get_current_user", "get_db", "get_db_session"]
