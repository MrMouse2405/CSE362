"""
Service layer package for the room-booking system.

This package encapsulates the core business logic and authentication integrations
of the application, separating them from the routing and data access layers.
It contains modules for user management, authentication strategies, and other
business workflows.
"""

from .booking_service import (
    BookingConflictError,
    BookingNotFoundError,
    BookingServiceError,
    BookingStateError,
    approve_booking,
    cancel_booking,
    deny_booking,
    get_all_bookings,
    get_pending_bookings,
    get_user_bookings,
    submit_booking,
)
from .notification_service import (
    NotificationNotFoundError,
    NotificationServiceError,
    get_notification_for_user,
    get_notifications,
    get_unread_count,
    mark_read,
    send_notification,
)

from .room_service import (
    RoomNotFoundError,
    RoomServiceError,
)

__all__ = [
    "BookingServiceError",
    "BookingNotFoundError",
    "BookingConflictError",
    "BookingStateError",
    "submit_booking",
    "approve_booking",
    "deny_booking",
    "cancel_booking",
    "get_user_bookings",
    "get_all_bookings",
    "get_pending_bookings",
    "NotificationServiceError",
    "NotificationNotFoundError",
    "RoomServiceError",
    "RoomNotFoundError",
    "send_notification",
    "get_notifications",
    "get_notification_for_user",
    "mark_read",
    "get_unread_count",
]
