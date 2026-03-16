from datetime import date, time

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

import app.models  # noqa: F401
from app.database import get_session
from app.main import app
from app.models import (
    Booking,
    BookingStatus,
    Notification,
    NotificationType,
    Room,
    TimeSlot,
    TimeslotStatus,
)

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)


@pytest_asyncio.fixture(scope="function")
async def session():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(session: AsyncSession):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _register_and_login(
    client: AsyncClient, email: str, role: str = "student"
) -> dict[str, str]:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "role": role},
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/auth/login",
        data={"username": email, "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    return {
        "token": token,
        "id": me_response.json()["id"],
        "email": email,
    }


async def _create_room(session: AsyncSession, name: str = "A-203") -> Room:
    room = Room(name=name, capacity=30)
    session.add(room)
    await session.commit()
    await session.refresh(room)
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
async def test_post_bookings_available_slots_returns_201(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "student1@example.com")
    room = await _create_room(session)
    slot = await _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))

    response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-01",
            "slot_ids": [slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["roomID"] == room.id
    assert payload["status"] == "pending"
    assert [item["id"] for item in payload["timeSlots"]] == [slot.id]

    await session.refresh(slot)
    assert slot.status == TimeslotStatus.HELD


@pytest.mark.asyncio
async def test_post_bookings_conflicting_slot_returns_409(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "student2@example.com")
    room = await _create_room(session, "A-204")
    blocked_slot = await _create_slot(
        session,
        room.id,
        date(2026, 4, 1),
        time(10, 0),
        time(11, 0),
        status=TimeslotStatus.BOOKED,
    )

    response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-01",
            "slot_ids": [blocked_slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )

    assert response.status_code == 409
    assert "unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_post_bookings_weekly_recurrence_creates_expected_booking(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "teacher1@example.com", role="teacher")
    room = await _create_room(session, "A-205")
    slot_one = await _create_slot(
        session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0)
    )
    slot_two = await _create_slot(
        session, room.id, date(2026, 4, 8), time(9, 0), time(10, 0)
    )
    slot_three = await _create_slot(
        session, room.id, date(2026, 4, 15), time(9, 0), time(10, 0)
    )

    response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-01",
            "slot_ids": [slot_one.id],
            "recurrence_freq": "weekly",
            "recurrence_end_date": "2026-04-15",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["recurrenceFrequency"] == "weekly"
    assert payload["recurrenceEndDate"] == "2026-04-15"
    assert {item["id"] for item in payload["timeSlots"]} == {
        slot_one.id,
        slot_two.id,
        slot_three.id,
    }


@pytest.mark.asyncio
async def test_get_bookings_as_user_returns_only_own_bookings(
    client: AsyncClient, session: AsyncSession
):
    owner = await _register_and_login(client, "owner@example.com")
    other = await _register_and_login(client, "other@example.com")
    room = await _create_room(session, "A-206")
    owner_slot = await _create_slot(
        session, room.id, date(2026, 4, 2), time(9, 0), time(10, 0)
    )
    other_slot = await _create_slot(
        session, room.id, date(2026, 4, 2), time(10, 0), time(11, 0)
    )

    owner_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {owner['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-02",
            "slot_ids": [owner_slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    assert owner_response.status_code == 201

    other_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {other['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-02",
            "slot_ids": [other_slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    assert other_response.status_code == 201

    response = await client.get(
        "/api/bookings", headers={"Authorization": f"Bearer {owner['token']}"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["userID"] == owner["id"]


@pytest.mark.asyncio
async def test_get_pending_bookings_as_admin_returns_pending_list(
    client: AsyncClient, session: AsyncSession
):
    admin = await _register_and_login(client, "admin-bookings@example.com", role="admin")
    student = await _register_and_login(client, "student3@example.com")
    room = await _create_room(session, "A-207")
    pending_slot = await _create_slot(
        session, room.id, date(2026, 4, 3), time(9, 0), time(10, 0)
    )
    approved_slot = await _create_slot(
        session, room.id, date(2026, 4, 3), time(10, 0), time(11, 0)
    )

    pending_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {student['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-03",
            "slot_ids": [pending_slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    assert pending_response.status_code == 201

    approved_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {student['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-03",
            "slot_ids": [approved_slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    assert approved_response.status_code == 201
    approved_booking_id = approved_response.json()["id"]

    patch_response = await client.patch(
        f"/api/bookings/{approved_booking_id}",
        headers={"Authorization": f"Bearer {admin['token']}"},
        json={"action": "approve"},
    )
    assert patch_response.status_code == 200

    response = await client.get(
        "/api/bookings?status=pending",
        headers={"Authorization": f"Bearer {admin['token']}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_patch_approve_transitions_booking_and_creates_notification(
    client: AsyncClient, session: AsyncSession
):
    admin = await _register_and_login(client, "admin-approve@example.com", role="admin")
    student = await _register_and_login(client, "student4@example.com")
    room = await _create_room(session, "A-208")
    slot = await _create_slot(session, room.id, date(2026, 4, 4), time(9, 0), time(10, 0))

    create_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {student['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-04",
            "slot_ids": [slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    booking_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin['token']}"},
        json={"action": "approve"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    await session.refresh(slot)
    assert slot.status == TimeslotStatus.BOOKED

    notifications = (
        await session.exec(
            select(Notification).where(Notification.bookingID == booking_id)
        )
    ).all()
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.APPROVED


@pytest.mark.asyncio
async def test_patch_deny_releases_held_slots(
    client: AsyncClient, session: AsyncSession
):
    admin = await _register_and_login(client, "admin-deny@example.com", role="admin")
    student = await _register_and_login(client, "student5@example.com")
    room = await _create_room(session, "A-209")
    slot = await _create_slot(session, room.id, date(2026, 4, 5), time(9, 0), time(10, 0))

    create_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {student['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-05",
            "slot_ids": [slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    booking_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin['token']}"},
        json={"action": "deny"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "denied"

    await session.refresh(slot)
    assert slot.status == TimeslotStatus.AVAILABLE


@pytest.mark.asyncio
async def test_patch_as_non_admin_returns_403(
    client: AsyncClient, session: AsyncSession
):
    student = await _register_and_login(client, "student6@example.com")
    owner = await _register_and_login(client, "student7@example.com")
    room = await _create_room(session, "A-210")
    slot = await _create_slot(session, room.id, date(2026, 4, 6), time(9, 0), time(10, 0))

    create_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {owner['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-06",
            "slot_ids": [slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    booking_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {student['token']}"},
        json={"action": "approve"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_patch_cancel_on_approved_booking_releases_booked_slots(
    client: AsyncClient, session: AsyncSession
):
    admin = await _register_and_login(client, "admin-cancel@example.com", role="admin")
    student = await _register_and_login(client, "student8@example.com")
    room = await _create_room(session, "A-211")
    slot = await _create_slot(session, room.id, date(2026, 4, 7), time(9, 0), time(10, 0))

    create_response = await client.post(
        "/api/bookings",
        headers={"Authorization": f"Bearer {student['token']}"},
        json={
            "room_id": room.id,
            "date": "2026-04-07",
            "slot_ids": [slot.id],
            "recurrence_freq": "none",
            "recurrence_end_date": None,
        },
    )
    booking_id = create_response.json()["id"]

    approve_response = await client.patch(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin['token']}"},
        json={"action": "approve"},
    )
    assert approve_response.status_code == 200

    cancel_response = await client.patch(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin['token']}"},
        json={"action": "cancel"},
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    await session.refresh(slot)
    assert slot.status == TimeslotStatus.AVAILABLE

    booking = await session.get(Booking, booking_id)
    assert booking is not None
    assert booking.status == BookingStatus.CANCELLED
