"""
Models Barrel File.

This module consolidates all domain models and re-exports them.
It ensures that when `SQLModel.metadata.create_all(engine)` is called,
all models are correctly registered with SQLAlchemy's metadata.
"""

from .booking import Booking
from .notification import Notification
from .room import Room
from .time_slot import TimeSlot
from .user import User

__all__ = [
    "User",
    "Room",
    "TimeSlot",
    "Booking",
    "Notification",
]
