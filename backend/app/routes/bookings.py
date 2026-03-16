"""
Booking routing module.

Provides authenticated endpoints for submitting bookings, viewing bookings,
and administering booking lifecycle transitions.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import Booking, BookingStatus, NotificationType, RecurrenceFrequency, User
from app.services.auth import current_active_user, require_admin
from app.services.booking_service import (
    BookingConflictError,
    BookingNotFoundError,
    BookingServiceError,
    BookingStateError,
    approve_booking,
    cancel_booking,
    deny_booking,
    get_all_bookings,
    get_user_bookings,
    submit_booking,
)
from app.services.notification_service import send_notification

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


class TimeSlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    slot_date: date
    start_time: time
    end_time: time
    status: str
    booking_id: int | None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    userID: UUID
    submittedByRole: str
    roomID: int
    status: str
    recurrenceFrequency: str
    recurrenceEndDate: date | None
    createdAt: datetime
    timeSlots: list[TimeSlotRead]


class BookingCreate(BaseModel):
    room_id: int
    date: date
    slot_ids: list[int]
    recurrence_freq: Literal["none", "weekly"] = "none"
    recurrence_end_date: date | None = None


class BookingActionUpdate(BaseModel):
    action: Literal["approve", "deny", "cancel"]


def _translate_booking_error(exc: Exception) -> HTTPException:
    if isinstance(exc, BookingConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, BookingNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (BookingServiceError, BookingStateError, ValueError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingCreate,
    response: Response,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        booking = await session.run_sync(
            lambda sync_session: submit_booking(
                user=user,
                room_id=booking_in.room_id,
                slot_ids=booking_in.slot_ids,
                recurrence_freq=booking_in.recurrence_freq,
                recurrence_end_date=booking_in.recurrence_end_date,
                session=sync_session,
            )
        )
    except Exception as exc:
        raise _translate_booking_error(exc) from exc

    response.status_code = status.HTTP_201_CREATED
    return booking


@router.get("", response_model=list[BookingRead])
async def list_bookings(
    status_filter: str | None = Query(default=None, alias="status"),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        if user.role == "admin":
            return await session.run_sync(
                lambda sync_session: get_all_bookings(sync_session, status_filter)
            )
        return await session.run_sync(
            lambda sync_session: get_user_bookings(user.id, sync_session)
        )
    except Exception as exc:
        raise _translate_booking_error(exc) from exc


@router.patch("/{booking_id}", response_model=BookingRead)
async def update_booking(
    booking_id: int,
    booking_update: BookingActionUpdate,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    del admin_user
    action_to_service = {
        "approve": approve_booking,
        "deny": deny_booking,
        "cancel": cancel_booking,
    }
    action_to_notification = {
        "approve": NotificationType.APPROVED,
        "deny": NotificationType.DENIED,
        "cancel": NotificationType.CANCELLED,
    }

    try:
        booking = await session.run_sync(
            lambda sync_session: action_to_service[booking_update.action](
                booking_id, sync_session
            )
        )
        await session.run_sync(
            lambda sync_session: send_notification(
                booking.userID,
                booking.id,
                action_to_notification[booking_update.action],
                sync_session,
            )
        )
    except Exception as exc:
        raise _translate_booking_error(exc) from exc

    return booking
