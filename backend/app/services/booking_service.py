"""
Booking service workflow.

Handles booking submission, approval, denial, cancellation, and admin queue lookup.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models import (
    Booking,
    BookingStatus,
    NotificationType,
    RecurrenceFrequency,
    TimeSlot,
    TimeslotStatus,
    User,
)
from app.services.notification_service import send_notification


class BookingServiceError(ValueError):
    """Base booking workflow error."""


class BookingNotFoundError(BookingServiceError):
    """Raised when a booking or timeslot cannot be found."""


class BookingConflictError(BookingServiceError):
    """Raised when a slot cannot be booked because it is unavailable."""


class BookingStateError(BookingServiceError):
    """Raised when a booking lifecycle transition is invalid."""


def _get_booking(session: Session, booking_id: int) -> Booking:
    statement = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.timeSlots))
    )
    booking = session.exec(statement).first()
    if booking is None:
        raise BookingNotFoundError(f"Booking {booking_id} was not found.")
    return booking


def _get_slots_by_id(session: Session, slot_ids: list[int]) -> list[TimeSlot]:
    if not slot_ids:
        raise BookingServiceError("At least one slot id is required.")

    slots = list(session.exec(select(TimeSlot).where(TimeSlot.id.in_(slot_ids))))
    slots_by_id = {slot.id: slot for slot in slots}
    missing_ids = [slot_id for slot_id in slot_ids if slot_id not in slots_by_id]
    if missing_ids:
        missing = ", ".join(str(slot_id) for slot_id in missing_ids)
        raise BookingNotFoundError(f"TimeSlot(s) not found: {missing}")

    return [slots_by_id[slot_id] for slot_id in slot_ids]


def _resolve_recurrence(
    session: Session,
    anchor_slots: list[TimeSlot],
    recurrence_frequency: RecurrenceFrequency,
    recurrence_end_date,
) -> list[TimeSlot]:
    if recurrence_frequency != RecurrenceFrequency.WEEKLY:
        return anchor_slots

    target_slots: list[TimeSlot] = []

    for slot in anchor_slots:
        current_date = slot.slot_date
        while current_date <= recurrence_end_date:
            if current_date == slot.slot_date:
                target_slots.append(slot)
            else:
                recurring_slot = session.exec(
                    select(TimeSlot).where(
                        TimeSlot.room_id == slot.room_id,
                        TimeSlot.slot_date == current_date,
                        TimeSlot.start_time == slot.start_time,
                        TimeSlot.end_time == slot.end_time,
                    )
                ).first()
                if recurring_slot is None:
                    raise BookingNotFoundError(
                        "Recurring timeslot not found for "
                        f"{current_date.isoformat()} {slot.start_time}-{slot.end_time}."
                    )
                target_slots.append(recurring_slot)

            current_date += timedelta(days=7)

    return target_slots


def submit_booking(
    user: User,
    room_id: int,
    slot_ids: list[int],
    recurrence_freq: str | RecurrenceFrequency,
    recurrence_end_date,
    session: Session,
) -> Booking:
    recurrence_frequency = RecurrenceFrequency(recurrence_freq)
    anchor_slots = _get_slots_by_id(session, slot_ids)

    for slot in anchor_slots:
        if slot.room_id != room_id:
            raise BookingConflictError(
                f"TimeSlot {slot.id} does not belong to room {room_id}."
            )

    if recurrence_frequency == RecurrenceFrequency.WEEKLY:
        if recurrence_end_date is None:
            raise BookingServiceError(
                "recurrence_end_date is required when recurrence_freq is weekly."
            )
        earliest_date = min(slot.slot_date for slot in anchor_slots)
        if recurrence_end_date < earliest_date:
            raise BookingServiceError(
                "recurrence_end_date must be on or after the anchor slot date."
            )
    elif recurrence_end_date is not None:
        raise BookingStateError(
            "recurrence_end_date can only be provided for weekly recurrence."
        )

    target_slots = _resolve_recurrence(
        session, anchor_slots, recurrence_frequency, recurrence_end_date
    )

    unavailable_slots = [
        slot.id for slot in target_slots if slot.status != TimeslotStatus.AVAILABLE
    ]
    if unavailable_slots:
        slot_list = ", ".join(str(slot_id) for slot_id in unavailable_slots)
        raise BookingConflictError(f"TimeSlot(s) unavailable: {slot_list}")

    for slot in target_slots:
        slot.hold()

    booking = Booking(
        userID=user.id,
        submittedByRole=user.role,
        roomID=room_id,
        status=BookingStatus.PENDING,
        recurrenceFrequency=recurrence_frequency,
        recurrenceEndDate=recurrence_end_date,
        timeSlots=target_slots,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return _get_booking(session, booking.id)


def approve_booking(booking_id: int, session: Session) -> Booking:
    booking = _get_booking(session, booking_id)
    if booking.status != BookingStatus.PENDING:
        raise BookingStateError("Only pending bookings can be approved.")

    invalid_slots = [
        slot.id for slot in booking.timeSlots if slot.status != TimeslotStatus.HELD
    ]
    if invalid_slots:
        slot_list = ", ".join(str(slot_id) for slot_id in invalid_slots)
        raise BookingStateError(f"Booking slots are not held: {slot_list}")

    for slot in booking.timeSlots:
        slot.book()

    booking.status = BookingStatus.APPROVED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return _get_booking(session, booking.id)


def deny_booking(booking_id: int, session: Session) -> Booking:
    booking = _get_booking(session, booking_id)
    if booking.status != BookingStatus.PENDING:
        raise BookingStateError("Only pending bookings can be denied.")

    invalid_slots = [
        slot.id for slot in booking.timeSlots if slot.status != TimeslotStatus.HELD
    ]
    if invalid_slots:
        slot_list = ", ".join(str(slot_id) for slot_id in invalid_slots)
        raise BookingStateError(f"Booking slots cannot be denied: {slot_list}")

    for slot in booking.timeSlots:
        slot.release()

    booking.status = BookingStatus.DENIED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return _get_booking(session, booking.id)


def cancel_booking(booking_id: int, session: Session) -> Booking:
    booking = _get_booking(session, booking_id)
    if booking.status != BookingStatus.APPROVED:
        raise BookingStateError("Only approved bookings can be cancelled.")

    invalid_slots = [
        slot.id for slot in booking.timeSlots if slot.status != TimeslotStatus.BOOKED
    ]
    if invalid_slots:
        slot_list = ", ".join(str(slot_id) for slot_id in invalid_slots)
        raise BookingStateError(f"Booking slots cannot be cancelled: {slot_list}")

    for slot in booking.timeSlots:
        slot.release()

    booking.status = BookingStatus.CANCELLED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return _get_booking(session, booking.id)


def get_pending_bookings(session: Session) -> list[Booking]:
    statement = (
        select(Booking)
        .where(Booking.status == BookingStatus.PENDING)
        .options(selectinload(Booking.timeSlots))
    )
    return list(session.exec(statement))


def get_user_bookings(
    user_id, session: Session, status: str | BookingStatus | None = None
) -> list[Booking]:
    statement = (
        select(Booking)
        .where(Booking.userID == user_id)
        .options(selectinload(Booking.timeSlots))
    )
    if status is not None:
        statement = statement.where(Booking.status == BookingStatus(status))

    statement = statement.order_by(Booking.createdAt.desc(), Booking.id.desc())
    return list(session.exec(statement))


def get_all_bookings(
    session: Session, status: str | BookingStatus | None = None
) -> list[Booking]:
    statement = select(Booking).options(selectinload(Booking.timeSlots))
    if status is not None:
        statement = statement.where(Booking.status == BookingStatus(status))

    statement = statement.order_by(Booking.createdAt.desc(), Booking.id.desc())
    return list(session.exec(statement))


_ACTION_MAP: dict[str, tuple] = {
    "approve": (approve_booking, NotificationType.APPROVED),
    "deny": (deny_booking, NotificationType.DENIED),
    "cancel": (cancel_booking, NotificationType.CANCELLED),
}


def process_booking_action(booking_id: int, action: str, session: Session) -> Booking:
    """Execute a booking lifecycle action and send the corresponding notification."""
    action_fn, notification_type = _ACTION_MAP[action]
    booking = action_fn(booking_id, session)
    send_notification(booking.userID, booking.id, notification_type, session)
    return booking
