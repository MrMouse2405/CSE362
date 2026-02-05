from enum import Enum
from sqlmodel import Field, SQLModel


class RecordStatus(str, Enum):
    """
    The three possible states a record can be in.
    """
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ARCHIVED = "archived"


class Record(SQLModel, table=True):
    """
    A Record represents a piece of work that moves through a workflow.

    The `table=True` parameter tells SQLModel to create a database table
    for this class. Each instance of Record = one row in the table.
    """

    # Primary key - auto-generated when you create a new record
    # None before saving to database, then gets assigned an integer ID
    id: int | None = Field(default=None, primary_key=True)

    # Title must be unique (enforced in service layer, not here)
    # index=True makes database lookups by title faster
    title: str = Field(index=True)

    # Optional description - defaults to empty string
    details: str = Field(default="")

    # Status starts as DRAFT for all new records
    status: RecordStatus = Field(default=RecordStatus.DRAFT)

    def submit(self):
        """
        Transition: draft → submitted
        """
        if self.status != RecordStatus.DRAFT:
            raise ValueError("Only draft records can be submitted.")
        self.status = RecordStatus.SUBMITTED

    def archive(self):
        """
        Transition: submitted → archived
        """
        if self.status != RecordStatus.SUBMITTED:
            raise ValueError("Only submitted records can be archived.")
        self.status = RecordStatus.ARCHIVED

    def can_delete(self) -> bool:
        """
        Rule: Only draft records can be deleted.
        """
        return self.status == RecordStatus.DRAFT

    def can_edit(self) -> bool:
        """
        Rule: Only draft records can be edited.
        """
        return self.status == RecordStatus.DRAFT

