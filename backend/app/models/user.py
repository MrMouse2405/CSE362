"""
User model — from ISS-01

Extends the fastapi-users SQLModel base user with a role attribute
that determines access level and booking-request tagging.

Traces to: UC-1, UC-5 | Domain class: User
"""

import enum
import uuid

from fastapi_users_db_sqlmodel import SQLModelBaseUserDB
from pydantic import field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field


class UserRole(str, enum.Enum):
    """Allowed roles for a User in the room-booking system."""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(SQLModelBaseUserDB, table=True):
    """
    Represents any authenticated person in the system.

    Inherits from SQLModelBaseUserDB which provides:
        id          – UUID, primary key
        email       – str, unique login identifier
        hashed_password – str
        is_active   – bool (default True)
        is_superuser – bool (default False)
        is_verified – bool (default False)

    Added by this model:
        role        – UserRole enum stored as a string (default "student")
    """

    role: UserRole = Field(default=UserRole.STUDENT)

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v: object) -> UserRole:
        """Ensure the role value is a valid UserRole member."""
        if isinstance(v, UserRole):
            return v
        try:
            return UserRole(v)
        except ValueError:
            allowed = ", ".join(r.value for r in UserRole)
            raise ValueError(f"Invalid role '{v}'. Must be one of: {allowed}")

    @classmethod
    async def deactivate_user(
        cls, user_id: uuid.UUID, session: AsyncSession
    ) -> "User | None":
        """
        Deactivates a user by setting their is_active status to False.

        Args:
            user_id (uuid.UUID): The UUID of the user to deactivate.
            session (AsyncSession): The asynchronous database session.

        Returns:
            User | None: The deactivated User object, or None if the user was not found.
        """
        user = await session.get(cls, user_id)
        if user:
            user.is_active = False
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user
