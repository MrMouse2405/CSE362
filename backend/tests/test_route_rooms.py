from datetime import date, time

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.main import app
from app.models.booking import TimeSlot, TimeslotStatus
from app.models.room import Room
from app.models.user import User, UserRole
from app.services.auth import current_active_user

# Setup in-memory SQLite for testing
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture
async def session():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(test_engine) as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def client(session: AsyncSession):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _create_user(session: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _create_room(
    session: AsyncSession, name: str = "A-203", capacity: int = 25
) -> Room:
    room = Room(name=name, capacity=capacity)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    assert room.id is not None
    session.expunge(room)
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
async def test_get_rooms_no_auth(client: AsyncClient):
    response = await client.get("/api/rooms?date=2026-05-01")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_rooms_with_auth(client: AsyncClient, session: AsyncSession):
    user = await _create_user(session)
    app.dependency_overrides[current_active_user] = lambda: user

    room = await _create_room(session)
    assert room.id is not None
    target_date = date(2026, 5, 1)
    await _create_slot(session, room.id, target_date, time(9, 0), time(10, 0))

    response = await client.get(f"/api/rooms?date={target_date.isoformat()}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == room.id
    assert len(data[0]["time_slots"]) == 1
    assert data[0]["time_slots"][0]["slot_date"] == target_date.isoformat()


@pytest.mark.asyncio
async def test_get_room_with_auth(client: AsyncClient, session: AsyncSession):
    user = await _create_user(session)
    app.dependency_overrides[current_active_user] = lambda: user

    room = await _create_room(session, name="Found Room")

    response = await client.get(f"/api/rooms/{room.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room.id
    assert data["name"] == "Found Room"


@pytest.mark.asyncio
async def test_get_room_not_found(client: AsyncClient, session: AsyncSession):
    user = await _create_user(session)
    app.dependency_overrides[current_active_user] = lambda: user

    response = await client.get("/api/rooms/999")
    assert response.status_code == 404
