from __future__ import annotations
from typing import Optional
from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel

class Room(SQLModel, table=True):
    "A bookable physical space at the campus"
    id: Optional[int] = Field(default=None, primary_key=True)

    #Name must be required, unique, & NOT NULL
    #Must also be in a human-readable form, like A-203
    name: str = Field(sa_column=Column(String, unique=True, nullable=False))

    #Capacity is required and must be positive
    capacity: int = Field(nullable=False, ge=1)



