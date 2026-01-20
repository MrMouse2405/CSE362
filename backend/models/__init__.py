from sqlmodel import Session, SQLModel, create_engine

import models.users as users

engine = create_engine("sqlite:///database.db")
SQLModel.metadata.create_all(engine)


def make_db_session() -> Session:
    return Session(engine)


__all__ = ["make_db_session", "users"]
