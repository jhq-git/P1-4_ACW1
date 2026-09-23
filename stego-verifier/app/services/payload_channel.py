"""Write and read the XOR-encrypted header and body through a cover's slots.

The header uses keystream bits [0, 56) and the body uses the bits after it.
"""

import numpy as np

from app.config import BITS_PER_BYTE, HEADER_BYTES, HEADER_LSB_COUNT
from app.core.bits import bits_to_bytes, bytes_to_bits, xor_bits
from app.core.embedding import read_bits, write_bits
from app.core.layout import SlotLayout, header_slot_indices
from app.core.location import generate_keystream_bits
from app.core.payload import Header, unpack_header
from app.media.base import CoverMedia

HEADER_BITS = HEADER_BYTES * BITS_PER_BYTE


def embed_payload(cover: CoverMedia, layout: SlotLayout, location_key: bytes, header: bytes, body: bytes) -> CoverMedia:
    """Encrypt header and body with the keystream and write them into the cover."""
    header_bits, body_bits = _encrypt(location_key, header, body)
    slots = cover.read_slots()
    slots = write_bits(slots, layout.header_slots, header_bits, HEADER_LSB_COUNT)
    slots = write_bits(slots, layout.body_slots, body_bits, layout.lsb_count)
    return cover.with_slots(slots)


def read_header(cover: CoverMedia, location_key: bytes, start_slot: int) -> Header:
    """Decrypt the header at `start_slot`; raise PayloadMissingError if the magic does not match."""
    indices = header_slot_indices(start_slot, cover.slot_count)
    cipher_bits = read_bits(cover.read_slots(), indices, HEADER_LSB_COUNT, HEADER_BITS)
    keystream = generate_keystream_bits(location_key, HEADER_BITS)
    return unpack_header(bits_to_bytes(xor_bits(cipher_bits, keystream)))


def read_body(cover: CoverMedia, layout: SlotLayout, location_key: bytes, body_length: int) -> bytes:
    """Decrypt `body_length` bytes from the body slots."""
    body_bit_count = body_length * BITS_PER_BYTE
    cipher_bits = read_bits(cover.read_slots(), layout.body_slots, layout.lsb_count, body_bit_count)
    keystream = generate_keystream_bits(location_key, HEADER_BITS + body_bit_count)
    return bits_to_bytes(xor_bits(cipher_bits, keystream[HEADER_BITS:]))


def _encrypt(location_key: bytes, header: bytes, body: bytes) -> tuple[np.ndarray, np.ndarray]:
    message_bits = bytes_to_bits(header + body)
    cipher_bits = xor_bits(message_bits, generate_keystream_bits(location_key, message_bits.size))
    return cipher_bits[:HEADER_BITS], cipher_bits[HEADER_BITS:]
