from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

import app.models.users as users
import app.models.records as records

engine = None


def init_db(db_url):
    global engine
    assert engine is None, "Database already initialized"
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized")


def make_db_session() -> Session:
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return Session(engine)


__all__ = ["make_db_session", "users", "records", "init_db"]
