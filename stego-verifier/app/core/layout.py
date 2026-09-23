"""Which slots hold the header and body.

Slots are used sequentially from the start slot, wrapping to 0 at the end:
    header -> 56 slots at 1 bit each
    body   -> ceil(body_bits / k) slots at k bits each
"""

from dataclasses import dataclass

import numpy as np

from app.config import BITS_PER_BYTE, HEADER_SLOTS
from app.core.bits import slots_needed
from app.core.errors import InsufficientCapacityError


@dataclass(frozen=True)
class SlotLayout:
    start_slot: int
    lsb_count: int
    header_slots: np.ndarray
    body_slots: np.ndarray

    @property
    def total_slots(self) -> int:
        return self.header_slots.size + self.body_slots.size


def required_slot_count(lsb_count: int, body_length: int) -> int:
    """Slots needed for the header plus a body of `body_length` bytes."""
    return HEADER_SLOTS + slots_needed(body_length * BITS_PER_BYTE, lsb_count)


def header_slot_indices(start_slot: int, slot_count: int) -> np.ndarray:
    return _sequential_indices(start_slot, HEADER_SLOTS, slot_count)


def plan_layout(start_slot: int, slot_count: int, lsb_count: int, body_length: int) -> SlotLayout:
    """Build the slot layout, or raise InsufficientCapacityError if it does not fit."""
    ensure_capacity(slot_count, lsb_count, body_length)
    body_slot_count = slots_needed(body_length * BITS_PER_BYTE, lsb_count)
    body_start = start_slot + HEADER_SLOTS
    return SlotLayout(
        start_slot=start_slot,
        lsb_count=lsb_count,
        header_slots=header_slot_indices(start_slot, slot_count),
        body_slots=_sequential_indices(body_start, body_slot_count, slot_count),
    )


def ensure_capacity(slot_count: int, lsb_count: int, body_length: int) -> None:
    needed = required_slot_count(lsb_count, body_length)
    if needed > slot_count:
        raise InsufficientCapacityError(
            f"Cover has {slot_count:,} slots but the payload needs {needed:,} at {lsb_count} LSB(s)."
        )


def _sequential_indices(first: int, count: int, slot_count: int) -> np.ndarray:
    return (first + np.arange(count, dtype=np.int64)) % slot_count
