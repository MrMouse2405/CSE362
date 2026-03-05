"""
Room Model Module.

This module defines the `Room` entity for the room-booking system.
A room represents a physical space with a specific capacity.

Traces to: UC-2 | Domain class: Room
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class Room(SQLModel, table=True):
    """
    Represents a bookable physical space at the campus.

    Attributes:
        id (Optional[int]): The primary key of the room. Defaults to None.
        name (str): The human-readable name of the room (e.g., "A-203"). Must be unique.
        capacity (int): The maximum number of people the room can accommodate. Must be >= 1.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    # Name must be required, unique, & NOT NULL
    # Must also be in a human-readable form, like A-203
    name: str = Field(sa_column=Column(String, unique=True, nullable=False))

    # Capacity is required and must be positive
    capacity: int = Field(nullable=False, ge=1)
