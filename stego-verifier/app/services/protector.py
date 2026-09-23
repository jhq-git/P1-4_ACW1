"""Protect workflow: hash, sign and embed a verification payload into a cover."""

import os
import time
import uuid
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.config import MILLISECONDS_PER_SECOND, NONCE_BYTES
from app.core.hashing import compute_media_hash
from app.core.layout import SlotLayout, plan_layout
from app.core.location import derive_location_key, derive_start_slot
from app.core.payload import (
    Header,
    PayloadFields,
    compute_body_length,
    pack_header,
    serialize_content,
    validate_text_fields,
)
from app.core.signing import load_private_key, sign
from app.media.base import CoverMedia
from app.media.loader import load_cover
from app.services.payload_channel import embed_payload
from app.services.validation import validate_lsb_count, validate_new_secret_key


@dataclass(frozen=True)
class ProtectRequest:
    cover_bytes: bytes
    private_key_pem: bytes
    secret_key: str
    sender_name: str
    note: str
    lsb_count: int


@dataclass(frozen=True)
class ProtectResult:
    cover: CoverMedia
    stego: CoverMedia
    fields: PayloadFields
    layout: SlotLayout
    body_length: int
    signature: bytes


def protect(request: ProtectRequest) -> ProtectResult:
    """Run the full Protect workflow; raises StegoError subclasses on bad input."""
    _validate_request(request)
    cover = load_cover(request.cover_bytes)
    private_key = load_private_key(request.private_key_pem)
    location_key = derive_location_key(request.secret_key)
    body_length = compute_body_length(request.sender_name, request.note)
    layout = _plan(cover, location_key, request.lsb_count, body_length)
    fields = _build_fields(cover, layout, request.sender_name, request.note)
    content, signature = _sign_content(fields, private_key)
    header = pack_header(Header(lsb_count=request.lsb_count, body_length=body_length))
    stego = embed_payload(cover, layout, location_key, header, content + signature)
    return ProtectResult(cover, stego, fields, layout, body_length, signature)


def _validate_request(request: ProtectRequest) -> None:
    validate_lsb_count(request.lsb_count)
    validate_new_secret_key(request.secret_key)
    validate_text_fields(request.sender_name, request.note)


def _plan(cover: CoverMedia, location_key: bytes, lsb_count: int, body_length: int) -> SlotLayout:
    start_slot = derive_start_slot(location_key, cover.slot_count)
    return plan_layout(start_slot, cover.slot_count, lsb_count, body_length)


def _build_fields(cover: CoverMedia, layout: SlotLayout, sender_name: str, note: str) -> PayloadFields:
    return PayloadFields(
        media_type=cover.media_type,
        media_id=uuid.uuid4(),
        timestamp_ms=int(time.time() * MILLISECONDS_PER_SECOND),
        nonce=os.urandom(NONCE_BYTES),
        media_hash=compute_media_hash(cover, layout),
        sender_name=sender_name,
        note=note,
    )


def _sign_content(fields: PayloadFields, private_key: Ed25519PrivateKey) -> tuple[bytes, bytes]:
    content = serialize_content(fields)
    return content, sign(private_key, content)
