"""
Notification routing module.

Provides authenticated endpoints for retrieving notifications, checking the
unread badge count, and marking a notification as read.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import Notification, User
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


def _to_notif(notification: Notification) -> NotificationRead:
    """Convert an ORM Notification to a Pydantic model inside the sync context."""
    return NotificationRead.model_validate(notification)


def _to_notif_list(notifications: list[Notification]) -> list[NotificationRead]:
    return [_to_notif(n) for n in notifications]


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    return await session.run_sync(
        lambda sync_session: _to_notif_list(
            get_notifications(user.id, cast(Session, sync_session))
        )
    )


@router.get("/unread-count", response_model=UnreadCountRead)
async def unread_count(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    count = await session.run_sync(
        lambda sync_session: get_unread_count(user.id, cast(Session, sync_session))
    )
    return UnreadCountRead(count=count)


@router.get("/recent", response_model=list[NotificationRead])
async def recent_notifications(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Returns unread notifications created in the last 60 seconds.
    Used for real-time toast notifications.
    """
    one_minute_ago = datetime.utcnow() - timedelta(seconds=60)

    def _get_recent(sync_session: Session):
        from sqlmodel import select

        statement = select(Notification).where(
            Notification.userID == user.id,
            Notification.isRead.is_(False),
            Notification.createdAt >= one_minute_ago,
        )
        return _to_notif_list(list(sync_session.exec(statement)))

    return await session.run_sync(_get_recent)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def read_notification(
    notification_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        await session.run_sync(
            lambda sync_session: get_notification_for_user(
                notification_id, user.id, cast(Session, sync_session)
            )
        )
        return await session.run_sync(
            lambda sync_session: _to_notif(
                mark_read(notification_id, cast(Session, sync_session))
            )
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
