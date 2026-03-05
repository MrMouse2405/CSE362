"""
Booking Model Module.

Defines the `Booking` entity representing a confirmed reservation.
(Currently a stub model awaiting full implementation.)
"""

from sqlmodel import Field, SQLModel


class Booking(SQLModel, table=True):
    """
    Represents a confirmed room booking.
    """

    id: int | None = Field(default=None, primary_key=True)
    """The primary key of the booking. Defaults to `None`."""
