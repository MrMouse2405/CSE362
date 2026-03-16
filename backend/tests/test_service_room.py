from datetime import date, time

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.booking import TimeSlot, TimeslotStatus
from app.models.room import Room
from app.services.room_service import get_room, get_rooms_with_availability


@pytest.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def _create_room(
    session: AsyncSession, name: str = "A-203", capacity: int = 25
) -> Room:
    room = Room(name=name, capacity=capacity)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    assert room.id is not None
    return room


async def _create_slot(
    session: AsyncSession,
    room_id: int,
    slot_date: date,
    start: time,
    end: time,
    status: TimeslotStatus = TimeslotStatus.AVAILABLE,
) -> TimeSlot:
    slot = TimeSlot(
        room_id=room_id,
        slot_date=slot_date,
        start_time=start,
        end_time=end,
        status=status,
    )
    session.add(slot)
    await session.commit()
    await session.refresh(slot)
    return slot


@pytest.mark.asyncio
async def test_get_rooms_returns_rooms_with_capacity(session: AsyncSession):
    room1 = await _create_room(session, name="R1", capacity=10)
    room2 = await _create_room(session, name="R2", capacity=20)

    rooms = await get_rooms_with_availability(date(2026, 5, 1), session)

    assert len(rooms) == 2
    room_ids = {r.id for r in rooms}
    assert room1.id in room_ids
    assert room2.id in room_ids

    r1 = next(r for r in rooms if r.id == room1.id)
    assert r1.capacity == 10


@pytest.mark.asyncio
async def test_get_rooms_attaches_slots_for_date(session: AsyncSession):
    room = await _create_room(session)
    assert room.id is not None
    session.expunge(room)
    target_date = date(2026, 5, 1)
    other_date = date(2026, 5, 2)

    slot1 = await _create_slot(session, room.id, target_date, time(9, 0), time(10, 0))
    _ = await _create_slot(session, room.id, other_date, time(9, 0), time(10, 0))

    rooms = await get_rooms_with_availability(target_date, session)

    assert len(rooms) == 1
    result_room = rooms[0]

    assert hasattr(result_room, "time_slots")
    slots = result_room.time_slots

    assert len(slots) == 1
    assert slots[0].id == slot1.id
    assert slots[0].slot_date == target_date


@pytest.mark.asyncio
async def test_get_rooms_returns_empty_slots_if_none_exist(session: AsyncSession):
    _ = await _create_room(session)
    target_date = date(2026, 5, 1)

    rooms = await get_rooms_with_availability(target_date, session)

    assert len(rooms) == 1
    assert hasattr(rooms[0], "time_slots")
    assert rooms[0].time_slots == []


@pytest.mark.asyncio
async def test_get_room_returns_room_by_id(session: AsyncSession):
    room = await _create_room(session, name="Target Room")
    assert room.id is not None

    result = await get_room(room.id, session)

    assert result.id == room.id
    assert result.name == "Target Room"


@pytest.mark.asyncio
async def test_get_room_raises_not_found(session: AsyncSession):
    with pytest.raises(HTTPException) as exc:
        await get_room(999, session)

    assert exc.value.status_code == 404
