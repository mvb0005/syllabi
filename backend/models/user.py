"""User ORM model."""

import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, new_uuid


class UserRole(enum.StrEnum):
    """Allowed roles for a platform user."""

    student = "student"
    instructor = "instructor"
    admin = "admin"


class User(Base, TimestampMixin):
    """Platform user — student, instructor, or admin."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), nullable=False, default=UserRole.student
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
