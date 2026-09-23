"""Convert domain objects into API response models."""

import base64
from datetime import datetime, timezone
from pathlib import Path

from app.config import MILLISECONDS_PER_SECOND, STEGO_FILENAME_SUFFIX
from app.api.schemas import CheckView, PayloadView, ProtectResponse, VerifyResponse
from app.core.payload import PayloadFields
from app.services.protector import ProtectResult
from app.services.verdicts import VerificationReport

DEFAULT_FILENAME_STEM = "cover"
BASE64_TEXT_ENCODING = "ascii"
DIFFERENCE_MAP_KEY = "difference_map_png"


def present_payload(fields: PayloadFields) -> PayloadView:
    return PayloadView(
        media_type=fields.media_type.name.lower(),
        media_id=str(fields.media_id),
        timestamp_ms=fields.timestamp_ms,
        timestamp_iso=_format_timestamp(fields.timestamp_ms),
        nonce_hex=fields.nonce.hex(),
        media_hash_hex=fields.media_hash.hex(),
        sender_name=fields.sender_name,
        note=fields.note,
    )


def present_protect_result(result: ProtectResult, original_filename: str) -> ProtectResponse:
    stego = result.stego
    return ProtectResponse(
        stego_base64=_to_base64(stego.encode()),
        stego_filename=stego_filename(original_filename, stego.file_extension),
        mime_type=stego.mime_type,
        media_kind=stego.media_type.name.lower(),
        media_description=stego.describe(),
        slot_count=stego.slot_count,
        start_slot=result.layout.start_slot,
        lsb_count=result.layout.lsb_count,
        header_slots=result.layout.header_slots.size,
        body_slots=result.layout.body_slots.size,
        body_length=result.body_length,
        signature_hex=result.signature.hex(),
        payload=present_payload(result.fields),
    )


def present_verification(report: VerificationReport) -> VerifyResponse:
    return VerifyResponse(
        verdict=report.verdict.value,
        summary=report.summary,
        checks=[CheckView(name=c.name, status=c.status.value, detail=c.detail) for c in report.checks],
        media_kind=report.media_kind,
        media_description=report.media_description,
        slot_count=report.slot_count,
        start_slot=report.start_slot,
        lsb_count=report.lsb_count,
        body_length=report.body_length,
        payload=present_payload(report.fields) if report.fields else None,
        payload_verified=report.fields_verified,
        expected_hash_hex=_hex_or_none(report.expected_hash),
        computed_hash_hex=_hex_or_none(report.computed_hash),
    )


def stego_filename(original_filename: str, extension: str) -> str:
    stem = Path(original_filename or DEFAULT_FILENAME_STEM).stem
    return f"{stem}{STEGO_FILENAME_SUFFIX}{extension}"


def present_comparison(comparison: dict) -> dict:
    """Replace raw PNG bytes with base64 text so the result is JSON-safe."""
    if DIFFERENCE_MAP_KEY not in comparison:
        return comparison
    return {**comparison, DIFFERENCE_MAP_KEY: _to_base64(comparison[DIFFERENCE_MAP_KEY])}


def _to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode(BASE64_TEXT_ENCODING)


def _format_timestamp(timestamp_ms: int) -> str:
    moment = datetime.fromtimestamp(timestamp_ms / MILLISECONDS_PER_SECOND, tz=timezone.utc)
    return moment.isoformat(timespec="seconds")


def _hex_or_none(value: bytes | None) -> str | None:
    return value.hex() if value is not None else None
