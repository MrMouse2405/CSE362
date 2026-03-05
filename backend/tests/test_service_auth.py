import uuid

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI
from fastapi_users import schemas
from fastapi_users_db_sqlmodel import SQLModelUserDatabaseAsync
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User, UserRole
from app.services.auth import (
    auth_backend,
    fastapi_users,
    require_admin,
)
from app.services.user_manager import UserManager, get_user_db

# Setup in-memory SQLite for testing
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")


class UserCreate(schemas.BaseUserCreate):
    role: UserRole = UserRole.STUDENT


class UserRead(schemas.BaseUser[uuid.UUID]):
    role: UserRole


app = FastAPI()

# Register routes for testing auth
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)


@app.get("/admin-only")
async def admin_only_route(user: User = Depends(require_admin)):
    return {"message": "Hello admin"}


@pytest_asyncio.fixture
async def session():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(test_engine) as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def user_db(session: AsyncSession):
    yield SQLModelUserDatabaseAsync(session, User)


@pytest_asyncio.fixture
async def user_manager(user_db: SQLModelUserDatabaseAsync):
    yield UserManager(user_db)


@pytest_asyncio.fixture  # type: ignore
def client(session: AsyncSession):
    # Override get_user_db dependency to use the test session
    async def override_get_user_db():
        yield SQLModelUserDatabaseAsync(session, User)

    app.dependency_overrides[get_user_db] = override_get_user_db
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_user(user_manager: UserManager):
    user_create = UserCreate(email="test@example.com", password="password123")
    user = await user_manager.create(user_create)
    assert user.email == "test@example.com"
    # Password should be hashed
    assert user.hashed_password != "password123"
    assert user.role == UserRole.STUDENT
    assert user.is_active is True


@pytest.mark.asyncio
async def test_auth_valid_credentials(client: AsyncClient, user_manager: UserManager):
    user_create = UserCreate(email="auth@example.com", password="password123")
    await user_manager.create(user_create)

    response = await client.post(
        "/auth/jwt/login",
        data={"username": "auth@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_wrong_password(client: AsyncClient, user_manager: UserManager):
    user_create = UserCreate(email="wrong@example.com", password="password123")
    await user_manager.create(user_create)

    response = await client.post(
        "/auth/jwt/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"


@pytest.mark.asyncio
async def test_auth_deactivated_account(client: AsyncClient, user_manager: UserManager):
    user_create = UserCreate(email="deact@example.com", password="password123")
    user = await user_manager.create(user_create)

    # Deactivate
    user.is_active = False
    await user_manager.user_db.update(user, {"is_active": False})

    response = await client.post(
        "/auth/jwt/login",
        data={"username": "deact@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"


@pytest.mark.asyncio
async def test_require_admin_fails_for_student(
    client: AsyncClient, user_manager: UserManager
):
    user_create = UserCreate(
        email="student@example.com", password="password123", role=UserRole.STUDENT
    )
    await user_manager.create(user_create)

    # Login as student
    response = await client.post(
        "/auth/jwt/login",
        data={"username": "student@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]

    # Access admin route
    admin_response = await client.get(
        "/admin-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert admin_response.status_code == 403
    assert admin_response.json()["detail"] == "Admin role required"


@pytest.mark.asyncio
async def test_require_admin_passes(client: AsyncClient, user_manager: UserManager):
    user_create = UserCreate(
        email="admin@example.com", password="password123", role=UserRole.ADMIN
    )
    await user_manager.create(user_create)

    # Login as admin
    response = await client.post(
        "/auth/jwt/login",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]

    # Access admin route
    admin_response = await client.get(
        "/admin-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["message"] == "Hello admin"


@pytest.mark.asyncio
async def test_admin_update_user(user_manager: UserManager):
    user_create = UserCreate(email="todeactivate@example.com", password="password123")
    user = await user_manager.create(user_create)
    assert user.is_active is True

    # Test our function
    updated = await user_manager.admin_update_user(user.id, is_active=False)
    assert updated is not None
    assert updated.is_active is False
    assert updated.id == user.id

    # Verify via DB
    db_user = await user_manager.get(user.id)
    assert db_user.is_active is False
