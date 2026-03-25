"""
Notification routing module.

Provides authenticated endpoints for retrieving notifications, checking the
unread badge count, and marking a notification as read.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import User
from app.services.auth import current_active_user
from app.services.notification_service import (
    NotificationNotFoundError,
    get_notification_for_user,
    get_notifications,
    get_unread_count,
    mark_read,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bookingID: int
    message: str
    type: str
    isRead: bool
    createdAt: datetime


class UnreadCountRead(BaseModel):
    count: int



@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    return await session.run_sync(lambda sync_session: get_notifications(user.id, sync_session))


@router.get("/unread-count", response_model=UnreadCountRead)
async def unread_count(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    count = await session.run_sync(lambda sync_session: get_unread_count(user.id, sync_session))
    return UnreadCountRead(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def read_notification(
    notification_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        await session.run_sync(
            lambda sync_session: get_notification_for_user(
                notification_id, user.id, sync_session
            )
        )
        return await session.run_sync(
            lambda sync_session: mark_read(notification_id, sync_session)
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
