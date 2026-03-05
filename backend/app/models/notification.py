from sqlmodel import Field, SQLModel


class Notification(SQLModel, table=True):
    """Stub model for Notification"""

    id: int | None = Field(default=None, primary_key=True)
