"""Reading uploaded files with a size limit."""

from fastapi import UploadFile

from app.config import MAX_UPLOAD_BYTES
from app.core.errors import InputValidationError

BYTES_PER_MEGABYTE = 1024 * 1024


async def read_upload(upload: UploadFile, label: str) -> bytes:
    """Read an upload fully, rejecting files over MAX_UPLOAD_BYTES."""
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // BYTES_PER_MEGABYTE
        raise InputValidationError(f"{label} is larger than the {limit_mb} MB limit.")
    return data
