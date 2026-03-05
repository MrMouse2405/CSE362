"""
Domain models for the room-booking system.

This package contains the `SQLModel` definitions representing the core entities
of the application. All models are re-exported here for convenient importing
and to ensure proper registration with SQLAlchemy's metadata before database
initialization.

**Exports:**

- `User`: Represents an authenticated person in the system.
- `Room`: Represents a physical bookable space.
- `TimeSlot`: Represents a specific bookable time window for a room.
- `Booking`: Represents a confirmed reservation.
- `Notification`: Represents a system alert or message.
"""

from .booking import Booking
from .notification import Notification
from .room import Room
from .time_slot import TimeSlot
from .user import User, UserRole

__all__ = [
    "User",
    "UserRole",
    "Room",
    "TimeSlot",
    "Booking",
    "Notification",
]
