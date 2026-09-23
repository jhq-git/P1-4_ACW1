"""LSB replacement on a flat array of unsigned slot values.

The first bit of each k-bit group lands in bit (k - 1) of its slot.
"""

import numpy as np

from app.core.bits import group_bits_into_values, split_values_into_bits


def write_bits(slots: np.ndarray, indices: np.ndarray, bits: np.ndarray, bits_per_slot: int) -> np.ndarray:
    """Return a copy of `slots` with `bits` written into the low bits of `indices`."""
    values = group_bits_into_values(bits, bits_per_slot).astype(slots.dtype)
    updated = clear_low_bits(slots, indices, bits_per_slot)
    updated[indices] |= values
    return updated


def read_bits(slots: np.ndarray, indices: np.ndarray, bits_per_slot: int, bit_count: int) -> np.ndarray:
    """Read `bit_count` bits from the low bits of `indices`."""
    values = slots[indices] & _low_bits_mask(slots.dtype, bits_per_slot)
    return split_values_into_bits(values, bits_per_slot, bit_count)


def clear_low_bits(slots: np.ndarray, indices: np.ndarray, bits_per_slot: int) -> np.ndarray:
    """Return a copy of `slots` with the low `bits_per_slot` bits of `indices` set to 0."""
    cleared = slots.copy()
    cleared[indices] &= _keep_high_bits_mask(slots.dtype, bits_per_slot)
    return cleared


def _low_bits_mask(dtype: np.dtype, bits_per_slot: int):
    return np.dtype(dtype).type((1 << bits_per_slot) - 1)


def _keep_high_bits_mask(dtype: np.dtype, bits_per_slot: int):
    all_ones = np.iinfo(dtype).max
    return np.dtype(dtype).type(all_ones ^ ((1 << bits_per_slot) - 1))
