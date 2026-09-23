"""Media hash with the payload bits cleared.

Only the bits the payload occupies are zeroed (bit 0 of header slots, the low
k bits of body slots). Every other sample is hashed in full, so the hash of
the cover before embedding equals the hash of the stego file after.
"""

import hashlib

from app.config import HEADER_LSB_COUNT
from app.core.embedding import clear_low_bits
from app.core.layout import SlotLayout
from app.media.base import CoverMedia


def compute_media_hash(cover: CoverMedia, layout: SlotLayout) -> bytes:
    """SHA-256 over the cover's samples with the payload bits cleared."""
    slots = cover.read_slots()
    slots = clear_low_bits(slots, layout.header_slots, HEADER_LSB_COUNT)
    slots = clear_low_bits(slots, layout.body_slots, layout.lsb_count)
    return hashlib.sha256(cover.with_slots(slots).canonical_bytes()).digest()
