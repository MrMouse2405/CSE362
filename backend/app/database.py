"""
Database Connection Module.

This module initializes the asynchronous database engine and provides a dependency
for FastAPI to inject database sessions into route handlers.
"""

import os

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.env import get_database_url

_DATABASE_URL = os.environ.get("DATABASE_URL", get_database_url())
_connect_args = {"check_same_thread": False} if "sqlite" in _DATABASE_URL else {}

engine = create_async_engine(_DATABASE_URL, connect_args=_connect_args)
"""SQLModel Database Engine"""

logger.info("Database Engine Running.")


async def get_session():
    """
    Generator dependency that yields an asynchronous database session.
    """
    async with AsyncSession(engine) as session:
        yield session
