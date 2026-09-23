"""Conversions between bytes, bit arrays and multi-bit slot values.

All conversions are MSB-first: the first bit of a byte (or of a slot group)
is its most significant bit.
"""

import numpy as np

from app.config import BITS_PER_BYTE


def bytes_to_bits(data: bytes) -> np.ndarray:
    """Return the bits of `data` as a uint8 array of 0s and 1s."""
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def bits_to_bytes(bits: np.ndarray) -> bytes:
    """Pack a bit array (length divisible by 8) back into bytes."""
    if bits.size % BITS_PER_BYTE != 0:
        raise ValueError("Bit count must be a multiple of 8.")
    return np.packbits(bits.astype(np.uint8)).tobytes()


def xor_bits(bits: np.ndarray, keystream: np.ndarray) -> np.ndarray:
    """XOR two equal-length bit arrays."""
    return np.bitwise_xor(bits, keystream[: bits.size])


def group_bits_into_values(bits: np.ndarray, bits_per_value: int) -> np.ndarray:
    """Group bits into integers of `bits_per_value` bits, zero-padding the tail."""
    padded = _pad_to_multiple(bits, bits_per_value)
    groups = padded.reshape(-1, bits_per_value).astype(np.uint16)
    weights = _msb_first_weights(bits_per_value)
    return groups @ weights


def split_values_into_bits(values: np.ndarray, bits_per_value: int, bit_count: int) -> np.ndarray:
    """Expand integers into `bits_per_value` bits each and keep the first `bit_count`."""
    shifts = np.arange(bits_per_value - 1, -1, -1, dtype=np.uint16)
    expanded = (values.astype(np.uint16)[:, None] >> shifts) & 1
    return expanded.reshape(-1)[:bit_count].astype(np.uint8)


def slots_needed(bit_count: int, bits_per_slot: int) -> int:
    """Number of slots required to hold `bit_count` bits."""
    return -(-bit_count // bits_per_slot)


def _pad_to_multiple(bits: np.ndarray, multiple: int) -> np.ndarray:
    padding = (-bits.size) % multiple
    return np.concatenate([bits, np.zeros(padding, dtype=bits.dtype)])


def _msb_first_weights(bit_count: int) -> np.ndarray:
    return (1 << np.arange(bit_count - 1, -1, -1)).astype(np.uint16)
