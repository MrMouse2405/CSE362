from sqlmodel import select

from app.models import make_db_session
from app.models.records import Record, RecordStatus


def _normalize(title: str) -> str:
    """
    Normalize title for case-insensitive comparison.
    """
    return title.strip().lower()


def create_record_service(title: str, details: str = "") -> dict:
    """
    Create a new record with unique title validation.

    Returns dict with:
    - ok: True if created, False if validation failed
    - message: Human-readable result
    - record: The created Record object (or None if failed)
    """
    if not title.strip():
        return {"ok": False, "message": "Title is required.", "record": None}

    with make_db_session() as session:
        # Check for duplicate title (case-insensitive)
        # We fetch all records and check in Python - simple but not scalable
        # For a production app, you'd use a database constraint or query
        existing = session.exec(select(Record)).all()
        for r in existing:
            if _normalize(r.title) == _normalize(title):
                return {
                    "ok": False,
                    "message": "Title must be unique (case-insensitive).",
                    "record": None,
                }

        # Create and save the new record
        record = Record(title=title.strip(), details=details.strip())
        session.add(record)  # Stage the record for insertion
        session.commit()  # Actually write to database
        session.refresh(record)  # Reload to get the auto-generated ID
        return {"ok": True, "message": "Record created.", "record": record}


def list_records_service() -> list[Record]:
    """
    Return all records.
    """
    with make_db_session() as session:
        return list(session.exec(select(Record)).all())


def get_record_service(record_id: int) -> Record | None:
    """
    Get a single record by ID.

    Returns None if not found - the route handles the 404.
    """
    with make_db_session() as session:
        return session.get(Record, record_id)


def submit_record_service(record_id: int) -> dict:
    """
    Transition a record from draft to submitted.
    """
    with make_db_session() as session:
        record = session.get(Record, record_id)
        if not record:
            return {"ok": False, "message": "Record not found.", "record": None}

        try:
            record.submit()  # Model enforces the rule
            session.add(record)  # Mark as modified
            session.commit()  # Save to database
            session.refresh(record)
            return {"ok": True, "message": "Record submitted.", "record": record}
        except ValueError as e:
            # Model raised an error - pass the message through
            return {"ok": False, "message": str(e), "record": record}


def archive_record_service(record_id: int) -> dict:
    """
    Transition a record from submitted to archived.
    """
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
    """
    Delete a record if it's in draft status.

    Uses the model's can_delete() method to check the rule.
    """
    with make_db_session() as session:
        record = session.get(Record, record_id)
        if not record:
            return {"ok": False, "message": "Record not found."}

        if not record.can_delete():
            return {"ok": False, "message": "Only draft records can be deleted."}

        session.delete(record)  # Mark for deletion
        session.commit()  # Actually delete from database
        return {"ok": True, "message": "Record deleted."}


def edit_record_service(record_id: int, new_details: str) -> dict:
    """
    Edit record details. Only draft records can be edited.

    Uses the model's can_edit() method to check the rule.
    """
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