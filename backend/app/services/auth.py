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

from app.models.user import User, UserRole
from app.services.user_manager import get_user_manager

_SECRET = os.environ.get("JWT_SECRET", "default_secret")

bearer_transport = BearerTransport(tokenUrl="/api/auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """
    Provides the configured JWT strategy for issuing and validating tokens.
    """
    return JWTStrategy(secret=_SECRET, lifetime_seconds=3600)


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
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user
