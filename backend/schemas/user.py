"""Pydantic schemas for User resources."""

from pydantic import BaseModel, ConfigDict, EmailStr

from backend.models.user import UserRole


class LoginRequest(BaseModel):
    """Request body for the login endpoint."""

    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""

    sub: str  # user id
    role: str
    exp: int


class UserBase(BaseModel):
    """Fields shared by create and read schemas."""

    email: EmailStr
    full_name: str
    role: UserRole = UserRole.student


class UserCreate(UserBase):
    """Request body for creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Request body for updating a user (all fields optional)."""

    full_name: str | None = None
    is_active: bool | None = None


class UserPublic(UserBase):
    """User representation returned by the API — no password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
