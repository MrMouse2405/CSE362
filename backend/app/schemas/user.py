"""
User Schema Module.

Defines Pydantic schemas for the User model, primarily used by the
FastAPI-Users routers for data validation and serialization.
"""

import uuid

from fastapi_users import schemas
from pydantic import BaseModel

from app.models.user import UserRole


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading a user's details."""

    name: str
    role: UserRole


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user."""

    name: str = ""
    role: UserRole = UserRole.STUDENT


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating an existing user."""

    name: str | None = None
    role: UserRole | None = None


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user's role or status."""

    role: UserRole | None = None
    is_active: bool | None = None
