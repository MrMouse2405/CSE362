from sqlmodel import select

from app.models import make_db_session
from app.models.records import Record, RecordStatus


def create_record_service(title: str, details: str = "") -> dict:
    if not title.strip():
        return {"ok": False, "message": "Title is required.", "record": None}

    with make_db_session() as session:
        existing = session.exec(select(Record)).all()
        for r in existing:
            if r.title.strip().lower() == title.strip().lower():
                return {
                    "ok": False,
                    "message": "Title must be unique (case-insensitive).",
                    "record": None,
                }

        record = Record(title=title.strip(), details=details.strip())
        session.add(record)
        session.commit()
        session.refresh(record)
        return {"ok": True, "message": "Record created.", "record": record}


def list_records_service() -> list[Record]:
    with make_db_session() as session:
        return list(session.exec(select(Record)).all())


def get_record_service(record_id: int) -> Record | None:
    with make_db_session() as session:
        return session.get(Record, record_id)


def submit_record_service(record_id: int) -> dict:
    with make_db_session() as session:
        record = session.get(Record, record_id)
        if not record:
            return {"ok": False, "message": "Record not found.", "record": None}

        try:
            record.submit()
            session.add(record)
            session.commit()
            session.refresh(record)
            return {"ok": True, "message": "Record submitted.", "record": record}
        except ValueError as e:
            return {"ok": False, "message": str(e), "record": record}


def archive_record_service(record_id: int) -> dict:
    with make_db_session() as session:
        record = session.get(Record, record_id)
        if not record:
            return {"ok": False, "message": "Record not found.", "record": None}

        try:
            record.archive()
            session.add(record)
            session.commit()
            session.refresh(record)
            return {"ok": True, "message": "Record archived.", "record": record}
        except ValueError as e:
            return {"ok": False, "message": str(e), "record": record}


def delete_record_service(record_id: int) -> dict:
    with make_db_session() as session:
        record = session.get(Record, record_id)
        if not record:
            return {"ok": False, "message": "Record not found."}

        if not record.can_delete():
            return {"ok": False, "message": "Only draft records can be deleted."}

        session.delete(record)
        session.commit()
        return {"ok": True, "message": "Record deleted."}


def edit_record_service(record_id: int, new_details: str) -> dict:
    with make_db_session() as session:
        record = session.get(Record, record_id)
        if not record:
            return {"ok": False, "message": "Record not found.", "record": None}

        if not record.can_edit():
            return {"ok": False, "message": "Only draft records can be edited.", "record": record}

        record.details = new_details.strip()
        session.add(record)
        session.commit()
        session.refresh(record)
        return {"ok": True, "message": "Record updated.", "record": record}

def search_records_service(keyword: str) -> list[Record]:
    keyword = keyword.strip()
    if not keyword:
        return list_records_service()

    with make_db_session() as session:
        return list(
            session.exec(
                select(Record).where(Record.title.contains(keyword))
            ).all()
        )