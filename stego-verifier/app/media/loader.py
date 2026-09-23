"""Detect the file type from its signature and load the matching cover."""

from app.config import PNG_SIGNATURE, WAV_RIFF_TAG
from app.core.errors import MediaFormatError
from app.media.audio_cover import AudioCover
from app.media.base import CoverMedia
from app.media.image_cover import ImageCover


def load_cover(data: bytes) -> CoverMedia:
    """Load PNG or WAV bytes; raise MediaFormatError for anything else."""
    if not data:
        raise MediaFormatError("The uploaded file is empty.")
    if data.startswith(PNG_SIGNATURE):
        return ImageCover.from_bytes(data)
    if data.startswith(WAV_RIFF_TAG):
        return AudioCover.from_bytes(data)
    raise MediaFormatError("Unsupported file type: only PNG images and WAV audio are accepted.")
