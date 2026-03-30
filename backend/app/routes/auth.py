"""
Auth Routing Module.

Provides routing for user authentication, registration, and user management.
Combines auto-generated routers from `fastapi-users` with custom admin routes.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlmodel import select

from app.models.user import User
from app.schemas.user import AdminUserUpdate, UserCreate, UserRead
from app.services import avatar_service
from app.services.auth import (
    auth_backend,
    current_active_user,
    fastapi_users,
    require_admin,
)
from app.services.user_manager import UserManager, get_user_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Mount standard fastapi-users login/logout routes
router.include_router(fastapi_users.get_auth_router(auth_backend))

# Mount standard fastapi-users registration route
router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(current_active_user)):
    """
    Returns the current authenticated user's profile based on their token.
    """
    return user


@router.get("/users", response_model=list[UserRead])
async def list_users(
    admin_user: User = Depends(require_admin),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Admin-only route to list all users.
    """
    del admin_user
    session = user_manager.user_db.session  # type: ignore
    statement = select(User)
    results = await session.execute(statement)
    return results.scalars().all()


@router.patch("/users/{id}", response_model=UserRead)
async def update_user_admin(
    id: uuid.UUID,
    user_update: AdminUserUpdate,
    admin_user: User = Depends(require_admin),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Admin-only route to update a user's role or deactivate their account.
    """
    target_user = await user_manager.admin_update_user(
        id,
        role=user_update.role,
        is_active=user_update.is_active,
    )
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return target_user


@router.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    id: uuid.UUID,
    admin_user: User = Depends(require_admin),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Admin-only route to delete a user.
    """
    del admin_user
    user = await user_manager.get(id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await user_manager.delete(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_create: UserCreate,
    admin_user: User = Depends(require_admin),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Admin-only route to create a new user.
    """
    del admin_user
    try:
        user = await user_manager.create(user_create, safe=False)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/avatar")
async def get_avatar(user: User = Depends(current_active_user)):
    """
    Returns a deterministic SVG avatar for the given user ID.

    The image is generated on the fly but is identical for the same user_id,
    so it can be aggressively cached by the browser.
    """
    svg = avatar_service.generate(seed=str(user.id))
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
