import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.models import Notification, NotificationType, User, UserRole
from app.services.notification_service import (
    NotificationNotFoundError,
    get_notifications,
    get_unread_count,
    mark_read,
    send_notification,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


def _create_user(session: Session, role: UserRole = UserRole.STUDENT) -> User:
    user = User(email=f"{uuid.uuid4()}@example.com", hashed_password="hash", role=role)  # type: ignore[arg-type]
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_notification(
    session: Session,
    user_id,
    booking_id: int,
    notification_type: NotificationType,
    created_at: datetime,
    is_read: bool = False,
) -> Notification:
    notification = Notification(
        userID=user_id,
        bookingID=booking_id,
        message=f"seed {booking_id}",
        type=notification_type,
        isRead=is_read,
        createdAt=created_at,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def test_send_notification_creates_unread_record_with_generated_message(
    session: Session,
):
    user = _create_user(session)

    notification = send_notification(
        user_id=user.id,
        booking_id=5,
        notification_type=NotificationType.APPROVED,
        session=session,
    )

    assert notification.userID == user.id
    assert notification.bookingID == 5
    assert notification.type == NotificationType.APPROVED
    assert notification.message == "Your booking #5 has been approved"
    assert notification.isRead is False


def test_get_notifications_returns_newest_first(session: Session):
    user = _create_user(session)
    base_time = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    oldest = _create_notification(
        session,
        user.id,
        1,
        NotificationType.APPROVED,
        base_time,
    )
    newest = _create_notification(
        session,
        user.id,
        2,
        NotificationType.DENIED,
        base_time + timedelta(minutes=10),
    )
    middle = _create_notification(
        session,
        user.id,
        3,
        NotificationType.CANCELLED,
        base_time + timedelta(minutes=5),
    )

    notifications = get_notifications(user.id, session)

    assert [notification.id for notification in notifications] == [
        newest.id,
        middle.id,
        oldest.id,
    ]


def test_mark_read_flips_notification_state(session: Session):
    user = _create_user(session)
    notification = send_notification(
        user_id=user.id,
        booking_id=7,
        notification_type="denied",
        session=session,
    )

    updated = mark_read(notification.id, session)

    assert updated.isRead is True
    assert session.get(Notification, notification.id).isRead is True


def test_mark_read_missing_notification_raises_error(session: Session):
    with pytest.raises(NotificationNotFoundError, match="was not found"):
        mark_read(999, session)


def test_get_unread_count_reflects_created_and_read_notifications(session: Session):
    user = _create_user(session)
    first = send_notification(
        user_id=user.id,
        booking_id=10,
        notification_type="approved",
        session=session,
    )
    send_notification(
        user_id=user.id,
        booking_id=11,
        notification_type="cancelled",
        session=session,
    )
    other_user = _create_user(session, UserRole.TEACHER)
    send_notification(
        user_id=other_user.id,
        booking_id=12,
        notification_type="approved",
        session=session,
    )

    assert get_unread_count(user.id, session) == 2

    mark_read(first.id, session)

    assert get_unread_count(user.id, session) == 1
