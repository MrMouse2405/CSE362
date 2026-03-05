"""
TimeSlot Model Module.

Defines a `TimeSlot` model representing a bookable time window for a specific room and date.
Timeslots are the atomic unit of scheduling in this system and allow tracking for availability.

Traces to: UC-2, UC-3, UC-4 | Domain class: TimeSlot
"""

from datetime import date, time
from enum import Enum

from sqlmodel import Field, SQLModel


class TimeslotStatus(str, Enum):
    """
    Allowed states for a room timeslot in the room-booking system.
    """

    AVAILABLE = "available"
    """The timeslot is free to be held or booked."""
    HELD = "held"
    """The timeslot is temporarily reserved."""
    BOOKED = "booked"
    """The timeslot is fully confirmed and reserved."""


class TimeSlot(SQLModel, table=True):
    """
    Represents any room request or timeslot unit in the system.
    """

    id: int | None = Field(default=None, primary_key=True)
    """The primary key for the timeslot."""
    room_id: int = Field(foreign_key="room.id", nullable=False)
    """Foreign key linking to the associated `Room`."""
    slot_date: date = Field(nullable=False)
    """The specific date of the timeslot."""
    start_time: time = Field(nullable=False)
    """The start time of the timeslot window."""
    end_time: time = Field(nullable=False)
    """The end time of the timeslot window."""
    status: TimeslotStatus = Field(default=TimeslotStatus.AVAILABLE)
    """Current status of the slot (`available`, `held`, `booked`)."""
    booking_id: int | None = Field(default=None, foreign_key="booking.id")
    """Foreign key linking to a confirmed `Booking`."""

    def hold(self):
        """
        Temporarily reserve the room timeslot.
        """
        if self.status != TimeslotStatus.AVAILABLE:
            raise ValueError("Only available timeslots can be held.")
        self.status = TimeslotStatus.HELD

    def book(self):
        """
        Confirm a reservation for the room timeslot.
        """
        if self.status != TimeslotStatus.HELD:
            raise ValueError("Only held timeslots can be booked.")
        self.status = TimeslotStatus.BOOKED

    def release(self):
        """
        Cancel a reservation or hold on the room timeslot, freeing it.
        """
        if self.status != TimeslotStatus.HELD and self.status != TimeslotStatus.BOOKED:
            raise ValueError("Only held or booked timeslots can be released.")
        self.status = TimeslotStatus.AVAILABLE
