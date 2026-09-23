"""Response models returned by the HTTP API."""

from pydantic import BaseModel


class KeyPairResponse(BaseModel):
    private_pem: str
    public_pem: str


class InspectResponse(BaseModel):
    media_kind: str
    media_description: str
    slot_count: int


class LimitsResponse(BaseModel):
    header_slots: int
    min_body_bytes: int
    max_sender_bytes: int
    max_note_bytes: int
    min_lsb_count: int
    max_lsb_count: int
    min_secret_key_length: int


class PayloadView(BaseModel):
    media_type: str
    media_id: str
    timestamp_ms: int
    timestamp_iso: str
    nonce_hex: str
    media_hash_hex: str
    sender_name: str
    note: str


class ProtectResponse(BaseModel):
    stego_base64: str
    stego_filename: str
    mime_type: str
    media_kind: str
    media_description: str
    slot_count: int
    start_slot: int
    lsb_count: int
    header_slots: int
    body_slots: int
    body_length: int
    signature_hex: str
    payload: PayloadView


class CheckView(BaseModel):
    name: str
    status: str
    detail: str


class VerifyResponse(BaseModel):
    verdict: str
    summary: str
    checks: list[CheckView]
    media_kind: str | None
    media_description: str | None
    slot_count: int | None
    start_slot: int | None
    lsb_count: int | None
    body_length: int | None
    payload: PayloadView | None
    payload_verified: bool
    expected_hash_hex: str | None
    computed_hash_hex: str | None


class ErrorResponse(BaseModel):
    detail: str
