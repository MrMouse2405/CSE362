"""
Booking Model - Issue 04
Represents the user request to book one or more time slots in a room
Pending -> Approved/Denied/Cancelled
Supports WEEKLY recurring bookings
Traces to: UC-3, UC-4
Domain Class: Booking
"""

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel


class BookingStatus(str, Enum):
    """
    Allowed lifecycle statuses for any given booking.
    """

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"


class RecurrenceFrequency(str, Enum):
    """
    Allowed recurrence frequency values.
    """

    NONE = "none"
    WEEKLY = "weekly"


class Booking(SQLModel, table=True):
    """
    Represents the room booking request made by a given user.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    userID: UUID = Field(foreign_key="user.id", nullable=False)
    roomID: int = Field(foreign_key="room.id", nullable=False)
    status: BookingStatus = Field(default=BookingStatus.PENDING)
    recurrenceFrequency: RecurrenceFrequency = Field(default=RecurrenceFrequency.NONE)
    recurrenceEndDate: Optional[date] = Field(default=None, nullable=True)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # One Booking -> many TimeSlots
    timeSlots: List["TimeSlot"] = Relationship(back_populates="booking")  # noqa: F821

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, a: object) -> BookingStatus:
        """
        Ensure the status value is a valid BookingStatus.
        """
        if isinstance(a, BookingStatus):
            return a
        try:
            return BookingStatus(a)
        except ValueError:
            allowed = ", ".join(t.value for t in BookingStatus)
            raise ValueError(f"Invalid status '{a}'. Must be one of: {allowed}")

    @field_validator("recurrenceFrequency", mode="before")
    @classmethod
    def validate_recurrence_frequency(cls, a: object) -> RecurrenceFrequency:
        """
        Ensure the recurrenceFrequency value is a valid RecurrenceFrequency.
        """
        if isinstance(a, RecurrenceFrequency):
            return a
        try:
            return RecurrenceFrequency(a)
        except ValueError:
            allowed = ", ".join(t.value for t in RecurrenceFrequency)
            raise ValueError(f"Invalid recurrence '{a}'. Must be one of: {allowed}")

    @model_validator(mode="after")
    def validate_recurrence_end_date(self) -> "Booking":
        """
        Weekly bookings must supply a recurrenceEndDate.
        """
        if (
            self.recurrenceFrequency == RecurrenceFrequency.WEEKLY
            and self.recurrenceEndDate is None
        ):
            raise ValueError(
                "recurrenceEndDate must not be None when recurrenceFrequency is 'weekly'."
            )
        return self


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
    booking: Optional["Booking"] = Relationship(back_populates="timeSlots")  # noqa: F821
    """The Booking this timeslot belongs to, if any."""

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
