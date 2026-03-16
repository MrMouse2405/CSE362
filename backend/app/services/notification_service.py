"""
Notification service workflow.

Creates and retrieves in-app notifications for booking lifecycle events.
"""

from __future__ import annotations

from sqlmodel import Session, select

from app.models import Notification, NotificationType


class NotificationServiceError(ValueError):
    """Base notification service error."""


class NotificationNotFoundError(NotificationServiceError):
    """Raised when a notification cannot be found."""


def _build_message(notification_type: NotificationType, booking_id: int) -> str:
    return f"Your booking #{booking_id} has been {notification_type.value}"


def send_notification(
    user_id,
    booking_id: int,
    notification_type: str | NotificationType,
    session: Session,
) -> Notification:
    normalized_type = NotificationType(notification_type)
    notification = Notification(
        userID=user_id,
        bookingID=booking_id,
        message=_build_message(normalized_type, booking_id),
        type=normalized_type,
        isRead=False,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def get_notifications(user_id, session: Session) -> list[Notification]:
    statement = (
        select(Notification)
        .where(Notification.userID == user_id)
        .order_by(Notification.createdAt.desc(), Notification.id.desc())
    )
    return list(session.exec(statement))


def mark_read(notification_id: int, session: Session) -> Notification:
    notification = session.get(Notification, notification_id)
    if notification is None:
        raise NotificationNotFoundError(
            f"Notification {notification_id} was not found."
        )

    notification.isRead = True
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def get_unread_count(user_id, session: Session) -> int:
    statement = select(Notification).where(
        Notification.userID == user_id, Notification.isRead.is_(False)
    )
    return len(list(session.exec(statement)))
