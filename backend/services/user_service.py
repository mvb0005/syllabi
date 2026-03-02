"""User service — business logic for user management."""

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions import ConflictError, NotFoundError
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Handles all user-related database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialise with an async database session."""
        self._db = db

    async def create_user(self, payload: UserCreate) -> User:
        """Create and persist a new user.

        Args:
            payload: Validated user creation data including plaintext password.

        Returns:
            The newly created User ORM instance.

        Raises:
            ConflictError: If a user with the given email already exists.
        """
        existing = await self._db.scalar(select(User).where(User.email == payload.email))
        if existing is not None:
            raise ConflictError(f"User with email '{payload.email}' already exists")

        user = User(
            email=payload.email,
            hashed_password=_pwd_context.hash(payload.password),
            full_name=payload.full_name,
            role=payload.role,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def get_user(self, user_id: str) -> User:
        """Retrieve a user by primary key.

        Args:
            user_id: UUID string of the user to retrieve.

        Returns:
            The matching User ORM instance.

        Raises:
            NotFoundError: If no user with that ID exists.
        """
        user = await self._db.get(User, user_id)
        if user is None:
            raise NotFoundError("User", user_id)
        return user

    async def update_user(self, user_id: str, payload: UserUpdate) -> User:
        """Apply partial updates to a user.

        Args:
            user_id: UUID string of the user to update.
            payload: Fields to update (any None fields are skipped).

        Returns:
            The updated User ORM instance.

        Raises:
            NotFoundError: If no user with that ID exists.
        """
        user = await self.get_user(user_id)
        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Return True if the plaintext password matches the hash."""
        return bool(_pwd_context.verify(plain, hashed))
