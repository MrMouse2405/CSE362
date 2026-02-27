"""
User model — from ISS-01

Extends the fastapi-users SQLModel base user with a role attribute
that determines access level and booking-request tagging.

Traces to: UC-1, UC-5 | Domain class: User
"""

import enum
from sqlmodel import Field
from pydantic import field_validator
from fastapi_users_db_sqlmodel import SQLModelBaseUserDB


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
            raise ValueError(
                f"Invalid role '{v}'. Must be one of: {allowed}"
            )