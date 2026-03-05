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
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    """The primary key of the room."""

    name: str = Field(sa_column=Column(String, unique=True, nullable=False))
    """The human-readable name of the room (e.g., `"A-203"`). Must be unique."""

    capacity: int = Field(nullable=False, ge=1)
    """The maximum number of people the room can accommodate. Must be `>= 1`."""
