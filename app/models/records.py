from enum import Enum
from sqlmodel import Field, SQLModel


class RecordStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ARCHIVED = "archived"


class Record(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    details: str = Field(default="")
    status: RecordStatus = Field(default=RecordStatus.DRAFT)

    def submit(self):
        if self.status != RecordStatus.DRAFT:
            raise ValueError("Only draft records can be submitted.")
        self.status = RecordStatus.SUBMITTED

    def archive(self):
        if self.status != RecordStatus.SUBMITTED:
            raise ValueError("Only submitted records can be archived.")
        self.status = RecordStatus.ARCHIVED

    def can_delete(self) -> bool:
        return self.status == RecordStatus.DRAFT

    def can_edit(self) -> bool:
        return self.status == RecordStatus.DRAFT