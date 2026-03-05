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

    Attributes:
        AVAILABLE: The timeslot is free to be held or booked.
        HELD: The timeslot is temporarily reserved.
        BOOKED: The timeslot is fully confirmed and reserved.
    """

    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"


class TimeSlot(SQLModel, table=True):
    """
    Represents any room request or timeslot unit in the system.

    Attributes:
        id (int | None): The primary key for the timeslot.
        room_id (int): Foreign key linking to the associated Room.
        slot_date (date): The specific date of the timeslot.
        start_time (time): The start time of the timeslot window.
        end_time (time): The end time of the timeslot window.
        status (TimeslotStatus): Current status of the slot (available, held, booked).
        booking_id (int | None): Foreign key linking to a confirmed Booking.
    """

    id: int | None = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="room.id", nullable=False)
    slot_date: date = Field(nullable=False)
    start_time: time = Field(nullable=False)
    end_time: time = Field(nullable=False)
    status: TimeslotStatus = Field(default=TimeslotStatus.AVAILABLE)
    booking_id: int | None = Field(default=None, foreign_key="booking.id")

    def hold(self):
        """
        Temporarily reserve the room timeslot.

        Raises:
            ValueError: If the status is not TimeslotStatus.AVAILABLE.
        """
        if self.status != TimeslotStatus.AVAILABLE:
            raise ValueError("Only available timeslots can be held.")
        self.status = TimeslotStatus.HELD

    def book(self):
        """
        Confirm a reservation for the room timeslot.

        Raises:
            ValueError: If the status is not TimeslotStatus.HELD.
        """
        if self.status != TimeslotStatus.HELD:
            raise ValueError("Only held timeslots can be booked.")
        self.status = TimeslotStatus.BOOKED

    def release(self):
        """
        Cancel a reservation or hold on the room timeslot, freeing it.

        Raises:
            ValueError: If the status is not TimeslotStatus.HELD or TimeslotStatus.BOOKED.
        """
        if self.status != TimeslotStatus.HELD and self.status != TimeslotStatus.BOOKED:
            raise ValueError("Only held or booked timeslots can be released.")
        self.status = TimeslotStatus.AVAILABLE
