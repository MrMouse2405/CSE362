"""
Notifications Model - Issue 05
In-app message delivered to a user when their booking request is either
approved, denied, or cancelled. Notifications are stored and can be retrieved
via API. Email delivery is a future possible feature.
Traces to: UC-4, UC-6
Domain Class: Notification
"""

import enum
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class NotificationType(str, enum.Enum):
    """
    Allowed notification type values.
    """

    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"


class Notification(SQLModel, table=True):
    """
    Represents an in-app notification sent to a user about their booking.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    userID: UUID = Field(foreign_key="user.id", nullable=False)
    bookingID: int = Field(foreign_key="booking.id", nullable=False)
    message: str = Field(nullable=False)
    type: NotificationType = Field(nullable=False)
    isRead: bool = Field(default=False)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, a: object) -> NotificationType:
        """
        Ensure the type value is a valid NotificationType.
        """
        if isinstance(a, NotificationType):
            return a
        try:
            return NotificationType(a)
        except ValueError:
            allowed = ", ".join(t.value for t in NotificationType)
            raise ValueError(
                f"Invalid Notification Type '{a}'. Must be one of: {allowed}"
            )
