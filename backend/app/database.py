"""
Database Connection Module.

This module initializes the asynchronous database engine and provides a dependency
for FastAPI to inject database sessions into route handlers.
"""

import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_async_engine(DATABASE_URL, connect_args=connect_args)


async def get_session():
    """
    Generator dependency that yields an asynchronous database session.

    Yields:
        AsyncSession: An asynchronous SQLModel/SQLAlchemy session.
    """
    async with AsyncSession(engine) as session:
        yield session
