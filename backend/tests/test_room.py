import pytest

from app.models.room import Room


def validate_room(data: dict) -> Room:
    if hasattr(Room, "model_validate"):
        return Room.model_validate(data)
    return Room.model_validate(data)


def test_creation_with_valid_attributes() -> None:
    room = validate_room({"name": "A204", "capacity": 25})
    assert room.name == "A204"
    assert room.capacity == 25
    assert room.id is None


def test_room_name_required() -> None:
    with pytest.raises(Exception):
        validate_room({"capacity": 10})


@pytest.mark.parametrize("bad_capacity", [0, -1, -10])
def test_room_capacity(bad_capacity: int) -> None:
    with pytest.raises(Exception):
        validate_room({"name": "A-203", "capacity": "bad_capacity"})
