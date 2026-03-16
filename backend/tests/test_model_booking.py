"""
Tests for the Booking Model
Covers:
    -Instantiation
    -Status validation
    -Recurrence validation
    -Default vals
    -No dependency on routes or services
"""

import uuid
from datetime import date, datetime, timezone

import pytest

from app.models import Booking, BookingStatus, RecurrenceFrequency


def _make_booking(**overrides) -> Booking:
    """
    Returns a valid booking with any field being overrideable
    """
    defaults = dict(
        userID=uuid.uuid4(),
        roomID=1,
    )
    return Booking.model_validate({**defaults, **overrides})


# Instantiation and Defaults


class TestBookingDefaults:
    def test_status_defaults_to_pending(self):
        b = _make_booking()
        assert b.status == BookingStatus.PENDING

    def test_recurrence_frequency_defaults_to_none(self):
        b = _make_booking()
        assert b.recurrenceFrequency == RecurrenceFrequency.NONE

    def test_recurrence_end_date_defaults_to_none(self):
        b = _make_booking()
        assert b.recurrenceEndDate is None

    def test_id_defaults_to_none(self):
        b = _make_booking()
        assert b.id is None

    def test_created_at_is_autopopulated(self):
        bef = datetime.now(timezone.utc)
        b = _make_booking()
        aft = datetime.now(timezone.utc)

        created = b.createdAt
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        assert bef <= created <= aft

    def test_created_at_is_datetime(self):
        b = _make_booking()
        assert isinstance(b.createdAt, datetime)


# Valid instantiation w/ all fields


class TestBookingInstantiation:
    """
    Ensure a booking can be created with all valid attributes
    """

    def test_create_single_booking(self):
        """
        Non-recurring booking can have recurrenceEndDate as None
        """
        uid = uuid.uuid4()
        b = _make_booking(
            userID=uid,
            roomID=1,
            status=BookingStatus.PENDING,
            recurrenceFrequency=RecurrenceFrequency.NONE,
            recurrenceEndDate=None,
        )
        assert b.userID == uid
        assert b.roomID == 1
        assert b.recurrenceEndDate is None

    def test_create_weekly_booking_with_end_date(self):
        """
        Weekly booking must have a recurrence end date
        """
        end = date(2026, 5, 1)
        b = _make_booking(
            recurrenceFrequency=RecurrenceFrequency.WEEKLY,
            recurrenceEndDate=end,
        )
        assert b.recurrenceFrequency == RecurrenceFrequency.WEEKLY
        assert b.recurrenceEndDate == end


# Status validation


class TestBookingStatusValidation:
    @pytest.mark.parametrize(
        "status",
        [
            BookingStatus.PENDING,
            BookingStatus.APPROVED,
            BookingStatus.DENIED,
            BookingStatus.CANCELLED,
        ],
    )
    def test_valid_status_enum(self, status: BookingStatus):
        b = _make_booking(status=status)
        assert b.status == status

    @pytest.mark.parametrize(
        "status_str", ["pending", "approved", "denied", "cancelled"]
    )
    def test_valid_status_string(self, status_str: str):
        b = _make_booking(status=status_str)
        assert b.status == status_str

    @pytest.mark.parametrize("bad_status", ["active", "PENDING", "Approved", " "])
    def test_invalid_status_raises(self, bad_status: str):
        with pytest.raises(Exception, match="Invalid status"):
            _make_booking(status=bad_status)


# Recurrence validation


class TestBookingRecurrenceValidation:
    @pytest.mark.parametrize("freq_str", ["none", "weekly"])
    def test_valid_recurrence_freq_string(self, freq_str: str):
        kwargs = {"recurrenceFrequency": freq_str}
        if freq_str == "weekly":
            kwargs["recurrenceEndDate"] = date(2026, 12, 31)  # type: ignore
        b = _make_booking(**kwargs)
        assert b.recurrenceFrequency == freq_str

    def test_weekly_without_end_date_raises(self):
        with pytest.raises(Exception, match="recurrenceEndDate must not be None"):
            _make_booking(
                recurrenceFrequency=RecurrenceFrequency.WEEKLY,
                recurrenceEndDate=None,
            )

    def test_none_freq_without_end_date_passes(self):
        b = _make_booking(
            recurrenceFrequency=RecurrenceFrequency.NONE, recurrenceEndDate=None
        )
        assert b.recurrenceEndDate is None

    @pytest.mark.parametrize("bad_freq", ["monthly", "daily", "WEEKLY", " "])
    def test_invalid_recurrence_freq_raises(self, bad_freq: str):
        with pytest.raises(Exception, match="Invalid recurrence"):
            _make_booking(recurrenceFrequency=bad_freq)
