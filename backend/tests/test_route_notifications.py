from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import app.models  # noqa: F401
from app.database import get_session
from app.main import app
from app.models import Notification, NotificationType

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

    return {"token": token, "id": UUID(me_response.json()["id"])}


async def _create_notification(
    session: AsyncSession,
    user_id,
    booking_id: int,
    notification_type: NotificationType,
    created_at: datetime,
    is_read: bool = False,
) -> Notification:
    notification = Notification(
        userID=user_id,
        bookingID=booking_id,
        message=f"seed {booking_id}",
        type=notification_type,
        isRead=is_read,
        createdAt=created_at,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification


@pytest.mark.asyncio
async def test_get_notifications_returns_users_notifications_newest_first(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "notify1@example.com")
    base_time = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    oldest = await _create_notification(
        session, user["id"], 1, NotificationType.APPROVED, base_time
    )
    newest = await _create_notification(
        session,
        user["id"],
        2,
        NotificationType.DENIED,
        base_time + timedelta(minutes=10),
    )
    middle = await _create_notification(
        session,
        user["id"],
        3,
        NotificationType.CANCELLED,
        base_time + timedelta(minutes=5),
    )

    response = await client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {user['token']}"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [newest.id, middle.id, oldest.id]


@pytest.mark.asyncio
async def test_get_notifications_does_not_return_other_users_notifications(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "notify2@example.com")
    other_user = await _register_and_login(client, "notify3@example.com")
    now = datetime(2026, 4, 2, 12, 0, tzinfo=timezone.utc)
    own_notification = await _create_notification(
        session, user["id"], 4, NotificationType.APPROVED, now
    )
    await _create_notification(
        session, other_user["id"], 5, NotificationType.DENIED, now + timedelta(minutes=1)
    )

    response = await client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {user['token']}"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [own_notification.id]


@pytest.mark.asyncio
async def test_get_unread_count_returns_correct_count(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "notify4@example.com")
    other_user = await _register_and_login(client, "notify5@example.com")
    now = datetime(2026, 4, 3, 12, 0, tzinfo=timezone.utc)
    await _create_notification(
        session, user["id"], 6, NotificationType.APPROVED, now, is_read=False
    )
    await _create_notification(
        session, user["id"], 7, NotificationType.CANCELLED, now, is_read=True
    )
    await _create_notification(
        session, user["id"], 8, NotificationType.DENIED, now, is_read=False
    )
    await _create_notification(
        session, other_user["id"], 9, NotificationType.APPROVED, now, is_read=False
    )

    response = await client.get(
        "/api/notifications/unread-count",
        headers={"Authorization": f"Bearer {user['token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {"count": 2}


@pytest.mark.asyncio
async def test_patch_read_marks_notification_as_read(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "notify6@example.com")
    notification = await _create_notification(
        session,
        user["id"],
        10,
        NotificationType.APPROVED,
        datetime(2026, 4, 4, 12, 0, tzinfo=timezone.utc),
    )

    response = await client.patch(
        f"/api/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {user['token']}"},
    )

    assert response.status_code == 200
    assert response.json()["isRead"] is True

    await session.refresh(notification)
    assert notification.isRead is True


@pytest.mark.asyncio
async def test_patch_read_other_users_notification_returns_404(
    client: AsyncClient, session: AsyncSession
):
    user = await _register_and_login(client, "notify7@example.com")
    other_user = await _register_and_login(client, "notify8@example.com")
    notification = await _create_notification(
        session,
        other_user["id"],
        11,
        NotificationType.DENIED,
        datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
    )

    response = await client.patch(
        f"/api/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {user['token']}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/notifications"),
        ("GET", "/api/notifications/unread-count"),
        ("PATCH", "/api/notifications/1/read"),
    ],
)
async def test_notification_endpoints_without_auth_return_401(
    client: AsyncClient, method: str, path: str
):
    response = await client.request(method, path)
    assert response.status_code == 401
