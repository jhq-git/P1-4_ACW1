"""Dispatch before/after comparisons to the image or audio visualizer."""

from app.core.errors import MediaFormatError
from app.media.audio_cover import AudioCover
from app.media.image_cover import ImageCover
from app.media.loader import load_cover
from app.visuals.audio_visuals import compare_audio
from app.visuals.image_visuals import compare_images


def compare_media(original_bytes: bytes, stego_bytes: bytes) -> dict:
    """Return comparison data keyed by media kind ('image' or 'audio')."""
    original = load_cover(original_bytes)
    stego = load_cover(stego_bytes)
    if isinstance(original, ImageCover) and isinstance(stego, ImageCover):
        return {"media_kind": "image", **compare_images(original, stego)}
    if isinstance(original, AudioCover) and isinstance(stego, AudioCover):
        return {"media_kind": "audio", **compare_audio(original, stego)}
    raise MediaFormatError("The original and stego files must both be images or both be audio.")

