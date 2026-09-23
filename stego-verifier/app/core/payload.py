"""Binary layout of the embedded header and body.

Header (7 B):  magic "STGO" | lsb_count | body_length
Body:          version | media_type | media_id | timestamp_ms | nonce | media_hash
               | sender_len | sender | note_len | note | signature (64 B)
The signature covers every body byte before it.
"""

import struct
import uuid
from dataclasses import dataclass
from enum import IntEnum

from app.config import (
    BYTE_ORDER,
    BODY_FIXED_STRUCT_FORMAT,
    HEADER_STRUCT_FORMAT,
    MAGIC,
    MAX_LSB_COUNT,
    MAX_NOTE_BYTES,
    MAX_SENDER_BYTES,
    MIN_LSB_COUNT,
    NOTE_LENGTH_BYTES,
    PAYLOAD_VERSION,
    SENDER_LENGTH_BYTES,
    SIGNATURE_BYTES,
    TEXT_ENCODING,
)
from app.core.errors import HeaderInvalidError, InputValidationError, PayloadFormatError, PayloadMissingError

BODY_FIXED_BYTES = struct.calcsize(BODY_FIXED_STRUCT_FORMAT)
MIN_BODY_BYTES = BODY_FIXED_BYTES + SENDER_LENGTH_BYTES + NOTE_LENGTH_BYTES + SIGNATURE_BYTES
MAX_BODY_BYTES = MIN_BODY_BYTES + MAX_SENDER_BYTES + MAX_NOTE_BYTES


class MediaType(IntEnum):
    IMAGE = 0
    AUDIO = 1


@dataclass(frozen=True)
class Header:
    lsb_count: int
    body_length: int


@dataclass(frozen=True)
class PayloadFields:
    media_type: MediaType
    media_id: uuid.UUID
    timestamp_ms: int
    nonce: bytes
    media_hash: bytes
    sender_name: str
    note: str


@dataclass(frozen=True)
class SignedBody:
    content: bytes
    signature: bytes


# --- Header ------------------------------------------------------------------

def pack_header(header: Header) -> bytes:
    return struct.pack(HEADER_STRUCT_FORMAT, MAGIC, header.lsb_count, header.body_length)


def unpack_header(data: bytes) -> Header:
    """Parse header bytes; raise PayloadMissingError if the magic does not match."""
    magic, lsb_count, body_length = struct.unpack(HEADER_STRUCT_FORMAT, data)
    if magic != MAGIC:
        raise PayloadMissingError("Magic 'STGO' not found at the derived start slot: no payload, or wrong secret key.")
    return Header(lsb_count=lsb_count, body_length=body_length)


def validate_header(header: Header) -> None:
    """Raise HeaderInvalidError if the header fields are out of range."""
    if not MIN_LSB_COUNT <= header.lsb_count <= MAX_LSB_COUNT:
        raise HeaderInvalidError(f"LSB count {header.lsb_count} is outside {MIN_LSB_COUNT}-{MAX_LSB_COUNT}.")
    if not MIN_BODY_BYTES <= header.body_length <= MAX_BODY_BYTES:
        raise HeaderInvalidError(
            f"Body length {header.body_length} B is outside {MIN_BODY_BYTES}-{MAX_BODY_BYTES} B."
        )


# --- Text fields -------------------------------------------------------------

def validate_text_fields(sender_name: str, note: str) -> None:
    """Raise InputValidationError if the sender or note exceed their byte limits."""
    _require_max_bytes("Sender name", sender_name, MAX_SENDER_BYTES)
    _require_max_bytes("Secret note", note, MAX_NOTE_BYTES)


def compute_body_length(sender_name: str, note: str) -> int:
    """Total body size in bytes, including the signature."""
    return MIN_BODY_BYTES + _encoded_length(sender_name) + _encoded_length(note)


# --- Body --------------------------------------------------------------------

def serialize_content(fields: PayloadFields) -> bytes:
    """Serialize every body field that the signature covers."""
    fixed = struct.pack(
        BODY_FIXED_STRUCT_FORMAT,
        PAYLOAD_VERSION,
        int(fields.media_type),
        fields.media_id.bytes,
        fields.timestamp_ms,
        fields.nonce,
        fields.media_hash,
    )
    sender = _length_prefixed(fields.sender_name, SENDER_LENGTH_BYTES)
    note = _length_prefixed(fields.note, NOTE_LENGTH_BYTES)
    return fixed + sender + note


def split_body(body: bytes) -> SignedBody:
    return SignedBody(content=body[:-SIGNATURE_BYTES], signature=body[-SIGNATURE_BYTES:])


def parse_content(content: bytes) -> PayloadFields:
    """Parse signed content bytes; raise PayloadFormatError if malformed."""
    try:
        return _parse_content_unchecked(content)
    except (struct.error, ValueError, UnicodeDecodeError) as error:
        raise PayloadFormatError(f"Payload fields are malformed: {error}") from error


def _parse_content_unchecked(content: bytes) -> PayloadFields:
    version, media_type, media_id, timestamp_ms, nonce, media_hash = struct.unpack_from(
        BODY_FIXED_STRUCT_FORMAT, content
    )
    if version != PAYLOAD_VERSION:
        raise ValueError(f"unsupported payload version {version}")
    sender_name, offset = _read_length_prefixed(content, BODY_FIXED_BYTES, SENDER_LENGTH_BYTES)
    note, offset = _read_length_prefixed(content, offset, NOTE_LENGTH_BYTES)
    if offset != len(content):
        raise ValueError("unexpected trailing bytes")
    return PayloadFields(
        media_type=MediaType(media_type),
        media_id=uuid.UUID(bytes=media_id),
        timestamp_ms=timestamp_ms,
        nonce=nonce,
        media_hash=media_hash,
        sender_name=sender_name,
        note=note,
    )


def _length_prefixed(text: str, prefix_bytes: int) -> bytes:
    encoded = text.encode(TEXT_ENCODING)
    return len(encoded).to_bytes(prefix_bytes, BYTE_ORDER) + encoded


def _read_length_prefixed(content: bytes, offset: int, prefix_bytes: int) -> tuple[str, int]:
    length_end = offset + prefix_bytes
    if length_end > len(content):
        raise ValueError("length prefix is truncated")
    length = int.from_bytes(content[offset:length_end], BYTE_ORDER)
    text_end = length_end + length
    if text_end > len(content):
        raise ValueError("text field is truncated")
    return content[length_end:text_end].decode(TEXT_ENCODING), text_end


def _encoded_length(text: str) -> int:
    return len(text.encode(TEXT_ENCODING))


def _require_max_bytes(label: str, text: str, max_bytes: int) -> None:
    if _encoded_length(text) > max_bytes:
        raise InputValidationError(f"{label} must be at most {max_bytes} bytes in UTF-8.")
