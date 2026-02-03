from typing import Annotated

from fastapi import APIRouter, Form, HTTPException
from pydantic.dataclasses import dataclass
from starlette.status import HTTP_404_NOT_FOUND

from app.services.records import (
    create_record_service,
    list_records_service,
    get_record_service,
    submit_record_service,
    archive_record_service,
    delete_record_service,
    edit_record_service,
)

# Create a router with a common prefix for all record routes
# All routes here will start with /api/v0/records/
router = APIRouter(
    prefix="/records",
    tags=["Records"],  # Groups these in API docs
)


@dataclass
class RecordResponse:
    """
    Response shape for a single record.
    """
    id: int
    title: str
    details: str
    status: str


@dataclass
class MessageResponse:
    """
    Standard response for operations that may succeed or fail.
    """
    ok: bool
    message: str
    record: RecordResponse | None = None


# ============================================================
# LIST ALL RECORDS
# ============================================================

@router.get(
    "",
    summary="List all records",
    description="Returns all records in the system.",
)
async def list_records() -> list[RecordResponse]:
    """
    GET /api/v0/records

    Returns an array of all records.
    """
    records = list_records_service()
    return [
        RecordResponse(
            id=r.id,
            title=r.title,
            details=r.details,
            status=r.status.value,  # Convert Enum to string
        )
        for r in records
    ]


# ============================================================
# GET SINGLE RECORD
# ============================================================

@router.get(
    "/{record_id}",
    summary="Get a record by ID",
    description="Returns a single record or 404 if not found.",
)
async def get_record(record_id: int) -> RecordResponse:
    """
    GET /api/v0/records/{id}

    The {record_id} in the path becomes a function parameter.
    FastAPI automatically validates it's an integer.
    """
    record = get_record_service(record_id)
    if not record:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Record not found")
    return RecordResponse(
        id=record.id,
        title=record.title,
        details=record.details,
        status=record.status.value,
    )


# ============================================================
# CREATE NEW RECORD
# ============================================================

@router.post(
    "",
    summary="Create a new record",
    description="Creates a new record. Title must be unique (case-insensitive).",
)
async def create_record(
        title: Annotated[str, Form()],
        details: Annotated[str, Form()] = "",
) -> MessageResponse:
    """
    POST /api/v0/records
    """
    outcome = create_record_service(title, details)

    # Convert model to response format (if record exists)
    record_response = None
    if outcome["record"]:
        r = outcome["record"]
        record_response = RecordResponse(
            id=r.id,
            title=r.title,
            details=r.details,
            status=r.status.value,
        )

    return MessageResponse(
        ok=outcome["ok"],
        message=outcome["message"],
        record=record_response,
    )


# ============================================================
# SUBMIT RECORD (draft → submitted)
# ============================================================

@router.post(
    "/{record_id}/submit",
    summary="Submit a record",
    description="Transitions a draft record to submitted status.",
)
async def submit_record(record_id: int) -> MessageResponse:
    """
    POST /api/v0/records/{id}/submit
    """
    outcome = submit_record_service(record_id)

    if not outcome["record"]:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=outcome["message"])

    r = outcome["record"]
    return MessageResponse(
        ok=outcome["ok"],
        message=outcome["message"],
        record=RecordResponse(
            id=r.id,
            title=r.title,
            details=r.details,
            status=r.status.value,
        ),
    )


# ============================================================
# ARCHIVE RECORD (submitted → archived)
# ============================================================

@router.post(
    "/{record_id}/archive",
    summary="Archive a record",
    description="Transitions a submitted record to archived status.",
)
async def archive_record(record_id: int) -> MessageResponse:
    """
    POST /api/v0/records/{id}/archive
    """
    outcome = archive_record_service(record_id)

    if not outcome["record"]:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=outcome["message"])

    r = outcome["record"]
    return MessageResponse(
        ok=outcome["ok"],
        message=outcome["message"],
        record=RecordResponse(
            id=r.id,
            title=r.title,
            details=r.details,
            status=r.status.value,
        ),
    )


# ============================================================
# DELETE RECORD
# ============================================================

@router.delete(
    "/{record_id}",
    summary="Delete a record",
    description="Deletes a record. Only draft records can be deleted.",
)
async def delete_record(record_id: int) -> MessageResponse:
    """
    DELETE /api/v0/records/{id}
    """
    outcome = delete_record_service(record_id)
    return MessageResponse(ok=outcome["ok"], message=outcome["message"], record=None)


# ============================================================
# EDIT RECORD DETAILS
# ============================================================

@router.patch(
    "/{record_id}",
    summary="Edit record details",
    description="Updates the details of a draft record.",
)
async def edit_record(
        record_id: int,
        details: Annotated[str, Form()],
) -> MessageResponse:
    """
    PATCH /api/v0/records/{id}
    """
    outcome = edit_record_service(record_id, details)

    if not outcome["record"]:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=outcome["message"])

    r = outcome["record"]
    return MessageResponse(
        ok=outcome["ok"],
        message=outcome["message"],
        record=RecordResponse(
            id=r.id,
            title=r.title,
            details=r.details,
            status=r.status.value,
        ),
    )