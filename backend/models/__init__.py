from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

import models.users as users
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)
logger.info("Database initialized")


def make_db_session() -> Session:
    return Session(engine)


__all__ = ["make_db_session", "users"]
