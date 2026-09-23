"""Media helper endpoints: limits, inspection and comparison."""

from fastapi import APIRouter, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.presenters import present_comparison
from app.api.schemas import InspectResponse, LimitsResponse
from app.api.uploads import read_upload
from app.config import (
    HEADER_SLOTS,
    MAX_LSB_COUNT,
    MAX_NOTE_BYTES,
    MAX_SENDER_BYTES,
    MIN_LSB_COUNT,
    MIN_SECRET_KEY_LENGTH,
)
from app.core.payload import MIN_BODY_BYTES
from app.media.loader import load_cover
from app.visuals.comparison import compare_media

router = APIRouter(prefix="/api", tags=["media"])


@router.get("/limits", response_model=LimitsResponse)
def get_limits() -> LimitsResponse:
    """Protocol limits the UI needs for validation and the capacity meter."""
    return LimitsResponse(
        header_slots=HEADER_SLOTS,
        min_body_bytes=MIN_BODY_BYTES,
        max_sender_bytes=MAX_SENDER_BYTES,
        max_note_bytes=MAX_NOTE_BYTES,
        min_lsb_count=MIN_LSB_COUNT,
        max_lsb_count=MAX_LSB_COUNT,
        min_secret_key_length=MIN_SECRET_KEY_LENGTH,
    )


@router.post("/inspect", response_model=InspectResponse)
async def inspect_media(file: UploadFile = File(...)) -> InspectResponse:
    """Describe a cover file and report its slot count."""
    cover = load_cover(await read_upload(file, "File"))
    return InspectResponse(
        media_kind=cover.media_type.name.lower(),
        media_description=cover.describe(),
        slot_count=cover.slot_count,
    )


@router.post("/compare")
async def compare(original: UploadFile = File(...), stego: UploadFile = File(...)) -> dict:
    original_bytes = await read_upload(original, "Original file")
    stego_bytes = await read_upload(stego, "Stego file")
    comparison = await run_in_threadpool(compare_media, original_bytes, stego_bytes)
    return present_comparison(comparison)

