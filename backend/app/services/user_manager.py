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

SECRET = os.environ.get("JWT_SECRET", "default_secret")


async def get_user_db(session: AsyncSession = Depends(get_session)):
    """
    Dependency yielding the SQLModel async database adapter for the User model.

    Args:
        session (AsyncSession): Database session injected by FastAPI.

    Yields:
        SQLModelUserDatabaseAsync: The async adapter configured with the current session.
    """
    yield SQLModelUserDatabaseAsync(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    Custom user manager that extends the base FastAPI-Users logic.
    Handles lifecycle hooks like post-registration logic.

    Attributes:
        reset_password_token_secret (str): Secret used to sign password reset tokens.
        verification_token_secret (str): Secret used to sign verification tokens.
    """

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """
        Lifecycle hook called automatically after a successful user registration.

        Args:
            user (User): The newly registered user.
            request (Optional[Request]): The current web request context.
        """
        print(f"User {user.id} has registered.")


async def get_user_manager(user_db: SQLModelUserDatabaseAsync = Depends(get_user_db)):
    """
    Dependency that yields a configured instance of `UserManager`.

    Args:
        user_db (SQLModelUserDatabaseAsync): The database adapter dependency.

    Yields:
        UserManager: Configured user manager.
    """
    yield UserManager(user_db)
