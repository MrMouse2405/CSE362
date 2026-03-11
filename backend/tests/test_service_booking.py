from datetime import date, time

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    Booking,
    BookingStatus,
    RecurrenceFrequency,
    Room,
    TimeSlot,
    TimeslotStatus,
    User,
    UserRole,
)
from app.services.booking_service import (
    BookingConflictError,
    BookingStateError,
    approve_booking,
    cancel_booking,
    deny_booking,
    get_pending_bookings,
    submit_booking,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


def _create_user(session: Session, role: UserRole = UserRole.STUDENT) -> User:
    user = User(email=f"{role.value}@example.com", hashed_password="hash", role=role)  # type: ignore[arg-type]
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_room(session: Session, name: str = "A-203") -> Room:
    room = Room(name=name, capacity=25)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def _create_slot(
    session: Session,
    room_id: int,
    slot_date: date,
    start: time,
    end: time,
    status: TimeslotStatus = TimeslotStatus.AVAILABLE,
) -> TimeSlot:
    slot = TimeSlot(
        room_id=room_id,
        slot_date=slot_date,
        start_time=start,
        end_time=end,
        status=status,
    )
    session.add(slot)
    session.commit()
    session.refresh(slot)
    return slot


def test_submit_booking_holds_available_slots_and_creates_pending_booking(session: Session):
    user = _create_user(session, UserRole.TEACHER)
    room = _create_room(session)
    slot_one = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    slot_two = _create_slot(session, room.id, date(2026, 4, 1), time(10, 0), time(11, 0))

    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot_one.id, slot_two.id],
        recurrence_freq=RecurrenceFrequency.NONE,
        recurrence_end_date=None,
        session=session,
    )

    session.refresh(slot_one)
    session.refresh(slot_two)

    assert booking.status == BookingStatus.PENDING
    assert booking.submittedByRole == UserRole.TEACHER
    assert booking.recurrenceFrequency == RecurrenceFrequency.NONE
    assert {slot.id for slot in booking.timeSlots} == {slot_one.id, slot_two.id}
    assert slot_one.status == TimeslotStatus.HELD
    assert slot_two.status == TimeslotStatus.HELD


def test_submit_booking_with_unavailable_slot_raises_conflict(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    open_slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    blocked_slot = _create_slot(
        session,
        room.id,
        date(2026, 4, 1),
        time(10, 0),
        time(11, 0),
        status=TimeslotStatus.BOOKED,
    )

    with pytest.raises(BookingConflictError, match="unavailable"):
        submit_booking(
            user=user,
            room_id=room.id,
            slot_ids=[open_slot.id, blocked_slot.id],
            recurrence_freq="none",
            recurrence_end_date=None,
            session=session,
        )

    session.refresh(open_slot)
    session.refresh(blocked_slot)
    assert open_slot.status == TimeslotStatus.AVAILABLE
    assert blocked_slot.status == TimeslotStatus.BOOKED


def test_submit_booking_with_weekly_recurrence_generates_all_matching_slots(
    session: Session,
):
    user = _create_user(session)
    room = _create_room(session)
    anchor_slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    week_two = _create_slot(session, room.id, date(2026, 4, 8), time(9, 0), time(10, 0))
    week_three = _create_slot(session, room.id, date(2026, 4, 15), time(9, 0), time(10, 0))

    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[anchor_slot.id],
        recurrence_freq="weekly",
        recurrence_end_date=date(2026, 4, 15),
        session=session,
    )

    assert booking.recurrenceFrequency == RecurrenceFrequency.WEEKLY
    assert booking.recurrenceEndDate == date(2026, 4, 15)
    assert {slot.id for slot in booking.timeSlots} == {
        anchor_slot.id,
        week_two.id,
        week_three.id,
    }


def test_submit_booking_with_weekly_recurrence_conflict_raises_error(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    anchor_slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    future_slot = _create_slot(
        session,
        room.id,
        date(2026, 4, 8),
        time(9, 0),
        time(10, 0),
        status=TimeslotStatus.HELD,
    )

    with pytest.raises(BookingConflictError, match="unavailable"):
        submit_booking(
            user=user,
            room_id=room.id,
            slot_ids=[anchor_slot.id],
            recurrence_freq="weekly",
            recurrence_end_date=date(2026, 4, 8),
            session=session,
        )

    session.refresh(anchor_slot)
    session.refresh(future_slot)
    assert anchor_slot.status == TimeslotStatus.AVAILABLE
    assert future_slot.status == TimeslotStatus.HELD


def test_approve_booking_books_held_slots(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )

    approved = approve_booking(booking.id, session)

    session.refresh(slot)
    assert approved.status == BookingStatus.APPROVED
    assert slot.status == TimeslotStatus.BOOKED


def test_approve_booking_when_slot_is_no_longer_held_raises_error(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )

    slot.status = TimeslotStatus.AVAILABLE
    session.add(slot)
    session.commit()

    with pytest.raises(BookingStateError, match="not held"):
        approve_booking(booking.id, session)


def test_deny_booking_releases_held_slots(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )

    denied = deny_booking(booking.id, session)

    session.refresh(slot)
    assert denied.status == BookingStatus.DENIED
    assert slot.status == TimeslotStatus.AVAILABLE


def test_cancel_booking_releases_booked_slots(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )
    approve_booking(booking.id, session)

    cancelled = cancel_booking(booking.id, session)

    session.refresh(slot)
    assert cancelled.status == BookingStatus.CANCELLED
    assert slot.status == TimeslotStatus.AVAILABLE


def test_get_pending_bookings_returns_only_pending_queue(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    pending_slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    approved_slot = _create_slot(session, room.id, date(2026, 4, 1), time(10, 0), time(11, 0))

    pending_booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[pending_slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )
    approved_booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[approved_slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )
    approve_booking(approved_booking.id, session)

    pending_bookings = get_pending_bookings(session)

    assert [booking.id for booking in pending_bookings] == [pending_booking.id]


def test_cancel_booking_from_pending_state_raises_error(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )

    with pytest.raises(BookingStateError, match="approved"):
        cancel_booking(booking.id, session)


def test_deny_booking_from_approved_state_raises_error(session: Session):
    user = _create_user(session)
    room = _create_room(session)
    slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))
    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )
    approve_booking(booking.id, session)

    with pytest.raises(BookingStateError, match="pending"):
        deny_booking(booking.id, session)


def test_booking_role_is_persisted_on_record(session: Session):
    user = _create_user(session, UserRole.ADMIN)
    room = _create_room(session)
    slot = _create_slot(session, room.id, date(2026, 4, 1), time(9, 0), time(10, 0))

    booking = submit_booking(
        user=user,
        room_id=room.id,
        slot_ids=[slot.id],
        recurrence_freq="none",
        recurrence_end_date=None,
        session=session,
    )

    stored_booking = session.exec(select(Booking).where(Booking.id == booking.id)).one()
    assert stored_booking.submittedByRole == UserRole.ADMIN
