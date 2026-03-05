"""
Authentication Module.

Configures the FastAPI-Users authentication backend using JWTs and Bearer transport.
It exports standard dependencies for extracting the current user and checking roles,
including custom roles like `admin`.
"""

import os
import uuid

from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.user_manager import get_user_manager

SECRET = os.environ.get("JWT_SECRET", "default_secret")

bearer_transport = BearerTransport(tokenUrl="/api/auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """
    Provides the configured JWT strategy for issuing and validating tokens.

    Returns:
        JWTStrategy: The configured strategy with a predefined secret and lifetime.
    """
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)


async def require_admin(user: User = Depends(current_active_user)) -> User | None:
    """
    Dependency to enforce admin-only access on specific routes.

    Args:
        user (User): The currently authenticated active user.

    Raises:
        HTTPException: 403 Forbidden if the user's role is not `admin`.

    Returns:
        User: The authenticated admin user.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


async def deactivate_user(user_id: uuid.UUID, session: AsyncSession) -> User | None:
    """
    Helper function to deactivate a user account by their UUID.

    Args:
        user_id (uuid.UUID): The UUID of the target user.
        session (AsyncSession): The asynchronous database session.

    Returns:
        User | None: The deactivated User object, or None if the user does not exist.
    """
    return await User.deactivate_user(user_id, session)
