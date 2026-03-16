"""
Rooms Routing Module.

Provides the two room-browsing endpoints used by the portal page:
  - GET /api/rooms?date={date}  — list all rooms with slot availability
  - GET /api/rooms/{id}         — fetch a single room by primary key

Both endpoints require a valid authenticated user (401 if missing).
Business logic is fully delegated to the room_service layer.

Traces to: UC-2
"""

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.room import RoomBasicRead, RoomRead
from app.services.auth import current_active_user
from app.services.room_service import get_room, get_rooms_with_availability

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=List[RoomRead])
async def list_rooms(
    target_date: date = Query(..., alias="date"),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Return all rooms with their time-slot availability for the requested date.

    The ``date`` query parameter is required. Each room in the response includes
    its name, capacity, and the list of time slots for that date (with
    ``start_time``, ``end_time``, and ``status``).  Rooms that have no slots
    on the given date are still returned but with an empty ``time_slots`` list.

    Requires a valid authenticated user — unauthenticated requests receive 401.
    """
    return await get_rooms_with_availability(target_date, session)


@router.get("/{id}", response_model=RoomBasicRead)
async def retrieve_room(
    id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Return the details of a single room identified by its integer primary key.

    Raises a 404 HTTP error if no room with the given ``id`` exists.
    Requires a valid authenticated user — unauthenticated requests receive 401.
    """
    return await get_room(id, session)
