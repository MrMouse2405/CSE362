"""
Database seed module.

Populates the database with rooms and time slots for February, March,
and April 2026. Each day gets a random subset of rooms, and each room
gets hourly time slots from 08:00 to 18:00.

This module is idempotent — it skips seeding if rooms already exist.
"""

import random
from datetime import date, time, timedelta

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import engine
from app.models.booking import TimeSlot
from app.models.room import Room

ROOMS = [
    {"name": "A-101", "capacity": 10},
    {"name": "A-102", "capacity": 15},
    {"name": "A-201", "capacity": 20},
    {"name": "A-202", "capacity": 8},
    {"name": "A-203", "capacity": 30},
    {"name": "B-101", "capacity": 12},
    {"name": "B-102", "capacity": 25},
    {"name": "B-201", "capacity": 6},
    {"name": "B-301", "capacity": 40},
    {"name": "C-101", "capacity": 18},
]

# Hourly slots from 08:00 to 18:00
SLOT_HOURS = [(time(h, 0), time(h + 1, 0)) for h in range(8, 18)]

# Months to seed: (year, month)
SEED_MONTHS = [(2026, 2), (2026, 3), (2026, 4)]

# Deterministic seed so the data is reproducible
RNG_SEED = 2026


# ── Helpers ────────────────────────────────────────────────────────────────


def _days_in_month(year: int, month: int) -> list[date]:
    """Return all dates in a given month."""
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1)
    else:
        last = date(year, month + 1, 1)
    return [first + timedelta(days=i) for i in range((last - first).days)]


# ── Main seed function ─────────────────────────────────────────────────────


async def seed_rooms_and_slots() -> None:
    """
    Populate the database with rooms and time slots.

    Idempotent: if any rooms already exist, the function returns early.
    """
    async with AsyncSession(engine) as session:
        # Check if rooms already exist
        existing = (await session.exec(select(Room).limit(1))).first()
        if existing:
            logger.info("Rooms already seeded — skipping.")
            return

        rng = random.Random(RNG_SEED)

        # 1. Create all rooms
        room_objects: list[Room] = []
        for room_data in ROOMS:
            room = Room(**room_data)
            session.add(room)
            room_objects.append(room)

        await session.flush()  # assigns IDs

        # 2. For each day in each month, pick a random subset of rooms
        #    and create hourly time slots for them.
        all_slots: list[TimeSlot] = []

        for year, month in SEED_MONTHS:
            for day in _days_in_month(year, month):
                # Pick 1–len(rooms) rooms available this day
                num_rooms = rng.randint(1, len(room_objects))
                day_rooms = rng.sample(room_objects, num_rooms)

                for room in day_rooms:
                    for start, end in SLOT_HOURS:
                        slot = TimeSlot(
                            room_id=room.id,  # type: ignore[arg-type]
                            slot_date=day,
                            start_time=start,
                            end_time=end,
                        )
                        all_slots.append(slot)

        session.add_all(all_slots)
        await session.commit()

        logger.info(
            f"Seeded {len(room_objects)} rooms and {len(all_slots)} time slots "
            f"across {len(SEED_MONTHS)} months."
        )
