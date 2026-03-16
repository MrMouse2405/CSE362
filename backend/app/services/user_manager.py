import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlmodel import SQLModelUserDatabaseAsync
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.env import get_super_user_email, get_super_user_name, get_super_user_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate


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

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """
        Lifecycle hook called automatically after a successful user registration.
        """
        # Swapped print for logger to keep your logging unified
        logger.info(f"User {user.id} has registered.")

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


async def register_superuser():
    """
    Creates a superuser on startup if one doesn't already exist.
    """
    name = get_super_user_name()
    email = get_super_user_email()
    password = get_super_user_password()

    # We must iterate the async generator to get the actual database session
    async for session in get_session():
        user_db = SQLModelUserDatabaseAsync(session, User)
        user_manager = UserManager(user_db)

        # Use the adapter to check if the user exists without throwing an exception
        user = await user_db.get_by_email(email)

        if user is None:
            logger.info(f"Creating superuser: {email}")
            user_create = UserCreate(
                name=name,
                email=email,
                password=password,
                role=UserRole.ADMIN,
            )
            # user_manager.create handles the password hashing
            user = await user_manager.create(user_create)
            logger.info(f"Superuser created: {user.name}#{user.id}")
        else:
            logger.info(f"Superuser already exists: {user.name}#{user.id}")

        # Break immediately so we only consume the first yielded session
        break
