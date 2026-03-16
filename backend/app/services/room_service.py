"""
Room Service Module.
This module provides services for retrieving room information and availability.
"""

from datetime import date
from typing import List

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import contains_eager
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.booking import TimeSlot
from app.models.room import Room


async def get_rooms_with_availability(
    target_date: date, session: AsyncSession
) -> List[Room]:
    """
    Query all Room records, then for each room, separately query the TimeSlots
    whose date matches the requested date. Return each room with its capacity
    and the list of slots (with their statuses).
    If no TimeSlots exist yet for a room on that date, returns the room with an empty slot list.
    """
    stmt = (
        select(Room)
        .outerjoin(
            TimeSlot,
            and_(Room.id == TimeSlot.room_id, TimeSlot.slot_date == target_date),  # type: ignore[arg-type]
        )
        .options(contains_eager(Room.time_slots))  # type: ignore[arg-type]
    )
    result = await session.exec(stmt)
    return list(result.unique().all())


async def get_room(room_id: int, session: AsyncSession) -> Room:
    """
    Return a single Room by its primary key, or raise an appropriate error
    (e.g. HTTPException 404) if no room with that ID exists.
    """
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room with ID {room_id} not found")
    return room
