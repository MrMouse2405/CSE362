"""
User Model Module.

This module defines the `User` entity, representing an authenticated person in the system.
It extends the base SQLModel user provided by `fastapi-users` by adding a role-based
attribute to handle different levels of system access.

Traces to: UC-1, UC-5 | Domain class: User
"""

import enum

from fastapi_users_db_sqlmodel import SQLModelBaseUserDB
from pydantic import field_validator
from sqlmodel import Field


class UserRole(str, enum.Enum):
    """
    Enumeration of allowed roles for a User in the room-booking system.
    """

    STUDENT = "student"
    """A standard user with base booking privileges."""
    TEACHER = "teacher"
    """An instructor user with elevated booking privileges."""
    ADMIN = "admin"
    """A system administrator with full access rights."""


class User(SQLModelBaseUserDB, table=True):
    """
    Represents any authenticated person in the system.

    This class inherits from `SQLModelBaseUserDB` which provides core authentication
    attributes, and it adds a specific role attribute for access control.
    """

    name: str = Field(default="")
    """The display name of the user. Defaults to empty string."""

    role: UserRole = Field(default=UserRole.STUDENT)
    """The system role of the user (e.g., student, teacher, admin). Defaults to `UserRole.STUDENT`."""

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v: object) -> UserRole:
        """
        Validates and coerces the incoming value for the user's role.
        """
        if isinstance(v, UserRole):
            return v
        try:
            return UserRole(v)
        except ValueError:
            allowed = ", ".join(r.value for r in UserRole)
            raise ValueError(f"Invalid role '{v}'. Must be one of: {allowed}")

