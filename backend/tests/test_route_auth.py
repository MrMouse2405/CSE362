import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.main import app
from app.models.user import User, UserRole

# Setup in-memory SQLite for testing
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)


@pytest_asyncio.fixture(scope="function")
async def session():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(test_engine) as session:
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


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    # Test POST /api/auth/register
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    # Create first
    await client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "role": "student",
        },
    )
    # Attempt duplicate
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_valid_credentials(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "role": "student",
        },
    )

    # Note: Login uses form data (username, password)
    response = await client.post(
        "/api/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_bad_credentials(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "email": "badlogin@example.com",
            "password": "password123",
            "role": "student",
        },
    )

    response = await client.post(
        "/api/auth/login",
        data={"username": "badlogin@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_me_valid_token(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "me@example.com", "password": "password123", "role": "student"},
    )

    login_res = await client.post(
        "/api/auth/login",
        data={"username": "me@example.com", "password": "password123"},
    )
    token = login_res.json()["access_token"]

    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_admin_unauthorized(client: AsyncClient):
    # Register student
    await client.post(
        "/api/auth/register",
        json={
            "email": "student@example.com",
            "password": "password123",
            "role": "student",
        },
    )
    login_res = await client.post(
        "/api/auth/login",
        data={"username": "student@example.com", "password": "password123"},
    )
    token = login_res.json()["access_token"]

    # Attempt to use admin patch
    target_id = login_res.json().get(
        "id"
    )  # Not actually returned on login, but let's just make one up

    # We need the user's ID, which we can get from /me
    me_res = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    user_id = me_res.json()["id"]

    response = await client.patch(
        f"/api/auth/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "teacher"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_admin_authorized(client: AsyncClient):
    # Register admin
    register_admin_res = await client.post(
        "/api/auth/register",
        json={"email": "admin@example.com", "password": "password123", "role": "admin"},
    )
    assert register_admin_res.status_code == 201

    # Login admin
    login_res = await client.post(
        "/api/auth/login",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_res.json()["access_token"]

    # Register target user
    target_res = await client.post(
        "/api/auth/register",
        json={
            "email": "target@example.com",
            "password": "password123",
            "role": "student",
        },
    )
    target_id = target_res.json()["id"]

    # Update target user as admin
    response = await client.patch(
        f"/api/auth/users/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "teacher", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "teacher"
    assert data["is_active"] is False
