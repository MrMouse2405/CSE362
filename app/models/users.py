from datetime import datetime
from enum import Enum

from pydantic.dataclasses import dataclass
from sqlmodel import Field, SQLModel


class Role(str, Enum):
    ROOT = "root"
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    UNASSIGNED = "unassigned"


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str
    password_hash: str
    role: Role = Field(default=Role.UNASSIGNED)


class Session(SQLModel, table=True):
    session_id: str = Field(default=None, primary_key=True)
    secret_hash: str = Field(default=None)
    created_at: datetime = Field(default=None)
    user_id: int = Field(foreign_key="user.id")


@dataclass
class SessionWithToken:
    session: Session
    token: str
