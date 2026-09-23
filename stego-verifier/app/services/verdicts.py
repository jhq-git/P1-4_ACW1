"""Verdicts, check statuses and the verification report model."""

from dataclasses import dataclass
from enum import Enum

from app.core.payload import PayloadFields


class Verdict(str, Enum):
    AUTHENTIC = "Authentic"
    TAMPERED = "Tampered"
    SIGNATURE_INVALID = "Signature Invalid"
    PAYLOAD_MISSING = "Payload Missing"
    CANNOT_VERIFY = "Cannot Verify"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


VERDICT_SUMMARIES = {
    Verdict.AUTHENTIC: "The payload is genuine and the media has not been modified.",
    Verdict.TAMPERED: "A payload was found, but the media or payload structure has been modified.",
    Verdict.SIGNATURE_INVALID: "The embedded payload was altered or was signed with a different key.",
    Verdict.PAYLOAD_MISSING: "No payload was found. The file is unprotected, or the secret key is wrong.",
    Verdict.CANNOT_VERIFY: "The file or key could not be processed, so verification was not possible.",
}

SKIPPED_DETAIL = "Not run because an earlier check failed."


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus
    detail: str


@dataclass
class VerificationReport:
    verdict: Verdict
    summary: str
    checks: list[CheckResult]
    media_kind: str | None = None
    media_description: str | None = None
    slot_count: int | None = None
    start_slot: int | None = None
    lsb_count: int | None = None
    body_length: int | None = None
    fields: PayloadFields | None = None
    fields_verified: bool = False
    expected_hash: bytes | None = None
    computed_hash: bytes | None = None
