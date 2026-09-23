"""Secret-key derivation for the payload start location and XOR keystream.

    K         = scrypt(secret_key, salt)
    start     = HMAC(K, "start")[:8] mod slot_count
    keystream = HMAC(K, "keystream" || 0) || HMAC(K, "keystream" || 1) || ...

The two labels provide domain separation so both values come from one K
without being related to each other.
"""

import hashlib
import hmac

import numpy as np
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from app.config import (
    BITS_PER_BYTE,
    BYTE_ORDER,
    KDF_SALT,
    KEYSTREAM_COUNTER_BYTES,
    KEYSTREAM_LABEL,
    LOCATION_KEY_BYTES,
    SCRYPT_BLOCK_SIZE,
    SCRYPT_COST,
    SCRYPT_PARALLELISM,
    START_DIGEST_BYTES,
    START_LABEL,
    TEXT_ENCODING,
)
from app.core.bits import bytes_to_bits

_HMAC_DIGEST = hashlib.sha256
_HMAC_DIGEST_BYTES = _HMAC_DIGEST().digest_size


def derive_location_key(secret_key: str) -> bytes:
    """Stretch the secret key into a 32-byte location key K with scrypt."""
    kdf = Scrypt(
        salt=KDF_SALT,
        length=LOCATION_KEY_BYTES,
        n=SCRYPT_COST,
        r=SCRYPT_BLOCK_SIZE,
        p=SCRYPT_PARALLELISM,
    )
    return kdf.derive(secret_key.encode(TEXT_ENCODING))


def derive_start_slot(location_key: bytes, slot_count: int) -> int:
    """Return the secret start slot index for a cover with `slot_count` slots."""
    digest = _hmac(location_key, START_LABEL)
    return int.from_bytes(digest[:START_DIGEST_BYTES], BYTE_ORDER) % slot_count


def generate_keystream_bits(location_key: bytes, bit_count: int) -> np.ndarray:
    """Return `bit_count` keystream bits in counter mode."""
    block_count = -(-bit_count // (_HMAC_DIGEST_BYTES * BITS_PER_BYTE))
    stream = b"".join(_keystream_block(location_key, counter) for counter in range(block_count))
    return bytes_to_bits(stream)[:bit_count]


def _keystream_block(location_key: bytes, counter: int) -> bytes:
    counter_bytes = counter.to_bytes(KEYSTREAM_COUNTER_BYTES, BYTE_ORDER)
    return _hmac(location_key, KEYSTREAM_LABEL + counter_bytes)


def _hmac(key: bytes, message: bytes) -> bytes:
    return hmac.new(key, message, _HMAC_DIGEST).digest()
