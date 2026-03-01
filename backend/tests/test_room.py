import pytest
from backend.app.models.room import Room

def test_creation_with_valid_attributes() -> None:
    room = Room(name="A204", capacity=25)
    assert room.name == "A204"
    assert room.capacity == 25
    assert room.id is None

def test_room_name_required() -> None:
    with pytest.raises(Exception):
        Room(capacity=10)

@pytest.mark.parametrize("bad_capacity", [0, -1, -10])
def test_room_capacity(bad_capacity: int) -> None:
    with pytest.raises(Exception):
        Room(name="A-203", capacity=bad_capacity)