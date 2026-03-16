from datetime import date, time
from typing import List

from sqlmodel import SQLModel

from app.models.booking import TimeslotStatus


class TimeSlotRead(SQLModel):
    id: int
    room_id: int
    slot_date: date
    start_time: time
    end_time: time
    status: TimeslotStatus


class RoomRead(SQLModel):
    id: int
    name: str
    capacity: int
    time_slots: List[TimeSlotRead] = []


class RoomBasicRead(SQLModel):
    id: int
    name: str
    capacity: int
