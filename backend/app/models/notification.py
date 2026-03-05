"""
Notification Model Module.

Defines the `Notification` entity representing system alerts or messages.
(Currently a stub model awaiting full implementation.)
"""

from sqlmodel import Field, SQLModel


class Notification(SQLModel, table=True):
    """
    Represents a system notification.

    Attributes:
        id (int | None): The primary key of the notification. Defaults to None.
    """

    id: int | None = Field(default=None, primary_key=True)
