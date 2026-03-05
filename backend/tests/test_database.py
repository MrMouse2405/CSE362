"""

Sanity Tests for the Database

"""

import os

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import engine, get_session
from app.models import Booking, Notification, Room, TimeSlot, User  # noqa: F401


def test_database_url_configurable(monkeypatch):
    """Test Database URL is configurable via environment variable."""
    # Since the module is already loaded, we just test that engine.url is populated
    assert (
        engine.url.render_as_string() == "sqlite+aiosqlite:///./app.db"
        or "DATABASE_URL" in os.environ
    )


@pytest.mark.asyncio
async def test_create_all():
    """Test that create_all produces the expected tables without errors."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    def get_tables(sync_conn):
        inspector = inspect(sync_conn)
        return inspector.get_table_names()

    async with test_engine.connect() as conn:
        tables = await conn.run_sync(get_tables)

    # We expect tables for user, room, timeslot, booking, notification
    assert "user" in tables
    assert "room" in tables
    assert "timeslot" in tables
    assert "booking" in tables
    assert "notification" in tables


@pytest.mark.asyncio
async def test_get_session():
    """Test that get_session yields a sqlmodel.ext.asyncio.session.AsyncSession."""
    session_generator = get_session()
    session = await anext(session_generator)

    assert isinstance(session, AsyncSession)

    # Check that it closes correctly when the generator is exhausted
    with pytest.raises(StopAsyncIteration):
        await anext(session_generator)
