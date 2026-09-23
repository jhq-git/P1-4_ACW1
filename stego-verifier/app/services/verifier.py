"""Verify workflow: an ordered list of checks where the first failure decides.

    1. Media & key format   -> Cannot Verify
    2. Payload header       -> Payload Missing
    3. Header fields        -> Tampered
    4. Digital signature    -> Signature Invalid
    5. Media hash           -> Tampered
    all pass                -> Authentic
"""

from dataclasses import dataclass
from typing import Callable

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.config import HEADER_SLOTS
from app.core.errors import HashMismatchError, MediaFormatError, PayloadFormatError, SignatureInvalidError, StegoError
from app.core.hashing import compute_media_hash
from app.core.layout import SlotLayout, plan_layout
from app.core.location import derive_location_key, derive_start_slot
from app.core.payload import Header, parse_content, split_body, validate_header
from app.core.signing import is_signature_valid, load_public_key
from app.media.base import CoverMedia
from app.media.loader import load_cover
from app.services.payload_channel import read_body, read_header
from app.services.validation import validate_secret_key_present
from app.services.verdicts import (
    SKIPPED_DETAIL,
    VERDICT_SUMMARIES,
    CheckResult,
    CheckStatus,
    VerificationReport,
    Verdict,
)


SIGNATURE_MISMATCH_DETAIL = "Ed25519 signature does not match: the payload was altered or signed by another key."


@dataclass(frozen=True)
class VerifyRequest:
    stego_bytes: bytes
    public_key_pem: bytes
    secret_key: str


@dataclass
class _VerificationState:
    """Values produced by earlier checks and consumed by later ones."""

    request: VerifyRequest
    report: VerificationReport
    cover: CoverMedia | None = None
    public_key: Ed25519PublicKey | None = None
    location_key: bytes | None = None
    header: Header | None = None
    layout: SlotLayout | None = None


@dataclass(frozen=True)
class _Check:
    name: str
    failure_verdict: Verdict
    run: Callable[[_VerificationState], str]


def verify(request: VerifyRequest) -> VerificationReport:
    """Run every check in order and return the verdict with a full report."""
    report = VerificationReport(verdict=Verdict.AUTHENTIC, summary="", checks=[])
    state = _VerificationState(request=request, report=report)
    for index, check in enumerate(_CHECKS):
        if not _run_check(check, state):
            _skip_remaining(report, _CHECKS[index + 1 :])
            return _finish(report, check.failure_verdict)
    report.fields_verified = True
    return _finish(report, Verdict.AUTHENTIC)


def _run_check(check: _Check, state: _VerificationState) -> bool:
    try:
        detail = check.run(state)
    except StegoError as error:
        state.report.checks.append(CheckResult(check.name, CheckStatus.FAILED, str(error)))
        return False
    state.report.checks.append(CheckResult(check.name, CheckStatus.PASSED, detail))
    return True


def _skip_remaining(report: VerificationReport, remaining: list[_Check]) -> None:
    report.checks.extend(CheckResult(check.name, CheckStatus.SKIPPED, SKIPPED_DETAIL) for check in remaining)


def _finish(report: VerificationReport, verdict: Verdict) -> VerificationReport:
    report.verdict = verdict
    report.summary = VERDICT_SUMMARIES[verdict]
    return report


# --- Checks ------------------------------------------------------------------

def _check_inputs(state: _VerificationState) -> str:
    validate_secret_key_present(state.request.secret_key)
    state.cover = load_cover(state.request.stego_bytes)
    state.public_key = load_public_key(state.request.public_key_pem)
    _record_media(state.report, state.cover)
    if state.cover.slot_count < HEADER_SLOTS:
        raise MediaFormatError(f"The file has only {state.cover.slot_count} slots; at least {HEADER_SLOTS} are needed.")
    return f"{state.cover.describe()} with {state.cover.slot_count:,} slots; public key is a valid Ed25519 key."


def _check_payload_header(state: _VerificationState) -> str:
    state.location_key = derive_location_key(state.request.secret_key)
    start_slot = derive_start_slot(state.location_key, state.cover.slot_count)
    state.report.start_slot = start_slot
    state.header = read_header(state.cover, state.location_key, start_slot)
    return f"Magic 'STGO' found at derived start slot {start_slot:,}."


def _check_header_fields(state: _VerificationState) -> str:
    header = state.header
    validate_header(header)
    state.report.lsb_count = header.lsb_count
    state.report.body_length = header.body_length
    state.layout = plan_layout(state.report.start_slot, state.cover.slot_count, header.lsb_count, header.body_length)
    return f"k = {header.lsb_count}; {header.body_length} B body across {state.layout.body_slots.size:,} slots."


def _check_signature(state: _VerificationState) -> str:
    body = read_body(state.cover, state.layout, state.location_key, state.header.body_length)
    signed = split_body(body)
    state.report.fields = _try_parse_fields(signed.content)
    if not is_signature_valid(state.public_key, signed.content, signed.signature):
        raise SignatureInvalidError(SIGNATURE_MISMATCH_DETAIL)
    state.report.fields = parse_content(signed.content)
    return "Ed25519 signature is valid for the supplied public key."


def _check_media_hash(state: _VerificationState) -> str:
    expected = state.report.fields.media_hash
    computed = compute_media_hash(state.cover, state.layout)
    state.report.expected_hash = expected
    state.report.computed_hash = computed
    if computed != expected:
        raise HashMismatchError("Recomputed SHA-256 differs from the signed hash: the media was modified.")
    return "Recomputed SHA-256 matches the signed hash."


def _record_media(report: VerificationReport, cover: CoverMedia) -> None:
    report.media_kind = cover.media_type.name.lower()
    report.media_description = cover.describe()
    report.slot_count = cover.slot_count


def _try_parse_fields(content: bytes):
    """Best-effort parse so unverified fields can still be shown with a warning."""
    try:
        return parse_content(content)
    except PayloadFormatError:
        return None


_CHECKS = [
    _Check("Media & key format", Verdict.CANNOT_VERIFY, _check_inputs),
    _Check("Payload header", Verdict.PAYLOAD_MISSING, _check_payload_header),
    _Check("Header fields", Verdict.TAMPERED, _check_header_fields),
    _Check("Digital signature", Verdict.SIGNATURE_INVALID, _check_signature),
    _Check("Media hash", Verdict.TAMPERED, _check_media_hash),
]
