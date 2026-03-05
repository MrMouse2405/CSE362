"""
Database Connection Module.

This module initializes the asynchronous database engine and provides a dependency
for FastAPI to inject database sessions into route handlers.
"""

import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
_connect_args = {"check_same_thread": False} if "sqlite" in _DATABASE_URL else {}


engine = create_async_engine(_DATABASE_URL, connect_args=_connect_args)
"""SQLModel Database Engine"""


async def get_session():
    """
    Generator dependency that yields an asynchronous database session.
    """
    async with AsyncSession(engine) as session:
        yield session
