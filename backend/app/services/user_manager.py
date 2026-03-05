"""
User Management Module.

Provides custom user managers to handle user CRUD operations via FastAPI-Users.
Wires up the SQLModel adapter to function completely asynchronously.
"""

import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlmodel import SQLModelUserDatabaseAsync
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User

_SECRET = os.environ.get("JWT_SECRET", "default_secret")


async def get_user_db(session: AsyncSession = Depends(get_session)):
    """
    Dependency yielding the `SQLModel` async database adapter for the `User` model.
    """
    yield SQLModelUserDatabaseAsync(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    Custom user manager that extends the base FastAPI-Users logic.
    Handles lifecycle hooks like post-registration logic.
    """

    reset_password_token_secret = _SECRET
    verification_token_secret = _SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """
        Lifecycle hook called automatically after a successful user registration.
        """
        print(f"User {user.id} has registered.")

    async def admin_update_user(
        self,
        user_id: uuid.UUID,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        """
        Admin-only service function to update a user's role or deactivate their account.
        """
        # Session is securely scoped inside user_db
        return await User.admin_update(
            user_id,
            self.user_db.session,  # type: ignore
            role=role,  # type: ignore
            is_active=is_active,
        )


async def get_user_manager(user_db: SQLModelUserDatabaseAsync = Depends(get_user_db)):
    """
    Dependency that yields a configured instance of `UserManager`.
    """
    yield UserManager(user_db)
