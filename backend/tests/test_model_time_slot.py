"""
Tests for the Timeslot model


Covers:
  • All valid transitions
  • Default status (available)
  • No dependency on routes or services
"""

import pytest
from datetime import date, time
from backend.app.models.time_slot import TimeSlot, TimeslotStatus


class TestValidTransitions:
    """Ensure all valid transitions function properly and invalid ones raise errors"""


    def test_hold_available_slot():
        slot = TimeSlot(id = 1, room_id = 1, Date = date.today(), start_time = time(9,0), end_time = time(10,0))
        assert slot.status == TimeslotStatus.AVAILABLE
        slot.hold()
        assert slot.status == TimeslotStatus.HELD


    def test_hold_held_slot():
        slot = TimeSlot(id = 2, room_id = 1, Date = date.today(), start_time = time(10,0), end_time = time(11,0), status = TimeslotStatus.HELD)
        with pytest.raises(ValueError):
            slot.hold()


    def test_hold_booked_slot():
        slot = TimeSlot(id = 2, room_id = 1, Date = date.today(), start_time = time(10,0), end_time = time(11,0), status = TimeslotStatus.BOOKED)
        with pytest.raises(ValueError):
            slot.hold()


    def test_book_held_slot():
        slot = TimeSlot(id = 3, room_id = 1, Date = date.today(), start_time = time(11,0), end_time = time(12,0), status = TimeslotStatus.HELD)
        slot.book()
        assert slot.status == TimeslotStatus.BOOKED


    def test_book_available_slot():
        slot = TimeSlot(id = 4, room_id = 1, Date = date.today(), start_time = time(12,0), end_time = time(13,0), status = TimeslotStatus.AVAILABLE)
        with pytest.raises(ValueError):
            slot.book()


    def test_book_booked_slot():
        slot = TimeSlot(id = 4, room_id = 1, Date = date.today(), start_time = time(12,0), end_time = time(13,0), status = TimeslotStatus.BOOKED)
        with pytest.raises(ValueError):
            slot.book()


    def test_release_booked_slot():
        slot = TimeSlot(id = 5, room_id = 1, Date = date.today(), start_time = time(13,0), end_time = time(14,0), status = TimeslotStatus.BOOKED)
        slot.release()
        assert slot.status == TimeslotStatus.AVAILABLE


    def test_release_held_slot():
        slot = TimeSlot(id = 6, room_id = 1, Date = date.today(), start_time = time(14,0), end_time = time(15,0), status = TimeslotStatus.HELD)
        slot.release()
        assert slot.status == TimeslotStatus.AVAILABLE


    def test_release_nonheld_nonbooked_slot():
        slot = TimeSlot(id = 7, room_id = 1, Date = date.today(), start_time = time(15,0), end_time = time(16,0), status = TimeslotStatus.AVAILABLE)
        with pytest.raises(ValueError):
            slot.release()


class TestRoomDefault:
    """Verifying default state for rooms is AVAILABLE."""


    def test_default_available():
        slot = TimeSlot(id = 8, room_id = 1, Date = date.today(), start_time = time(16,0), end_time = time(17,0))
        assert slot.status == TimeslotStatus.AVAILABLE
