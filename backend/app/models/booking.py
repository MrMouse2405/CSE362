from sqlmodel import Field, SQLModel


class Booking(SQLModel, table=True):
    """Stub model for Booking"""

    id: int | None = Field(default=None, primary_key=True)
