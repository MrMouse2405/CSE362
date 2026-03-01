"""
TimeSlot Model — from ISS-03


Defines a TimeSlot model representing a bookable time window for a specific room and date
Timeslots are the atomic unit of scheduling in this system and allow tracking for availability.


Traces to: UC-2, UC-3, UC-4 | Domain class: TimeSlot
"""

from enum import Enum
from sqlmodel import Field, SQLModel
from datetime import date, time


class TimeslotStatus(str, Enum):
    """Allowed states for a room in the room-booking system."""
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"


class TimeSlot(SQLModel, table=True):
    """
    Represents any room request in the system.


    Inherits from SQLModel
    """


    id: int | None = Field(default=None, primary_key=True)
    room_id: int = Field(default = "room.id", nullable=False)
    Date: date = Field(nullable=False)
    start_time: time = Field(nullable=False)
    end_time: time = Field(nullable=False)
    status: TimeslotStatus = Field(default="available")


    def hold(self):
        """Temporarily reserving the room, ensuring it is currently available before holding it."""
        if self.status != TimeslotStatus.AVAILABLE:
            raise ValueError("Only available timeslots can be held.")
        self.status = TimeslotStatus.HELD
   
    def book(self):
        """Reserving a room, ensuring it is currently held before booking it."""
        if self.status != TimeslotStatus.HELD:
            raise ValueError("Only held timeslots can be booked.")
        self.status = TimeslotStatus.BOOKED


    def release(self):
        """Unreserving a room, ensuring it is currently held or booked before releasing it."""
        if self.status != TimeslotStatus.HELD and self.status != TimeslotStatus.BOOKED:
            raise ValueError("Only held or booked timeslots can be released.")
        self.status = TimeslotStatus.AVAILABLE
