"""
Testing for the Notification Model
Covers:
    -Instantiation
    -Type validation
    -Default vals
    -No dependency on routes or services
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.notification import Notification, NotificationType


def _make_notification(**overrides) -> Notification:
    """
    Returns a valid notification with any field being overrideable
    """
    defaults = dict(
        userID=uuid.uuid4(),
        bookingID=1,
        message="Booking approved.",
        type=NotificationType.APPROVED,
    )
    return Notification(**{**defaults, **overrides})


# Instantiation and Defaults


class TestNotificationDefaults:
    def test_is_read_defaults_to_false(self):
        n = _make_notification()
        assert n.isRead is False

    def test_id_defaults_to_none(self):
        n = _make_notification()
        assert n.id is None

    def test_created_at_is_autopopulated(self):
        bef = datetime.now(timezone.utc)
        n = _make_notification()
        aft = datetime.now(timezone.utc)

        created = n.createdAt
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        assert bef <= created <= aft

    def test_created_at_is_datetime(self):
        n = _make_notification()
        assert isinstance(n.createdAt, datetime)


# Valid instantiation with all the fields
class TestNotificationInstantiation:
    """
    Ensure a notification can be created with all attributes being valid.
    """

    def test_create_with_valid_attributes(self):
        uid = uuid.uuid4()
        n = _make_notification(
            userID=uid,
            bookingID=1,
            message="Booking denied.",
            type=NotificationType.DENIED,
        )
        assert n.userID == uid
        assert n.bookingID == 1
        assert n.message == "Booking denied."
        assert n.type == NotificationType.DENIED

    def test_read_can_be_true(self):
        n = _make_notification(isRead=True)
        assert n.isRead is True


# Valid type assignment


class TestNotificationTypeAssignment:
    """
    Ensure each of the valid types can be set both via enum or
    as a raw string
    """

    @pytest.mark.parametrize(
        "ntype",
        [
            NotificationType.APPROVED,
            NotificationType.DENIED,
            NotificationType.CANCELLED,
        ],
    )
    def test_create_with_enum(self, ntype: NotificationType):
        n = _make_notification(type=ntype)
        assert n.type == ntype

    @pytest.mark.parametrize("type_str", ["approved", "denied", "cancelled"])
    def test_create_with_string(self, type_str: str):
        n = Notification.model_validate(
            {
                "userID": str(uuid.uuid4()),
                "bookingID": 1,
                "message": "Booking cancelled.",
                "type": type_str,
            }
        )
        assert n.type == NotificationType(type_str)


# Invalid values rejected


class TestNotificationTypeInvalid:
    """
    Type validation is done via a pydantic field_validator
    """

    @pytest.mark.parametrize(
        "bad_type",
        [
            "accepted",
            "DENIED",
            "Cancelled",
            " ",
        ],
    )
    def test_invalid_type(self, bad_type: str):
        with pytest.raises(Exception):
            Notification.model_validate(
                {
                    "userID": str(uuid.uuid4()),
                    "bookingID": 1,
                    "message": "Booking bugged.",
                    "type": bad_type,
                }
            )


# NotificationType enum Integrity


class TestNotificationEnumTypeIntegrity:
    """
    Ensure enum has exactly 3 members with expected vals
    """

    def test_enum_members(self):
        assert set(NotificationType) == {
            NotificationType.APPROVED,
            NotificationType.DENIED,
            NotificationType.CANCELLED,
        }

    def test_enum_values(self):
        assert NotificationType.APPROVED.value == "approved"
        assert NotificationType.DENIED.value == "denied"
        assert NotificationType.CANCELLED.value == "cancelled"

    def test_enum_str(self):
        # Enum vals should be usable as plain text strings'
        assert isinstance(NotificationType.APPROVED, str)
