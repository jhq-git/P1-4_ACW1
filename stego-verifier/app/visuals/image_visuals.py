"""Image comparison visuals: difference map and quality metrics."""

import io
import math

import numpy as np
from PIL import Image

from app.config import MAX_PIXEL_VALUE, METRIC_DECIMALS
from app.core.errors import MediaFormatError
from app.media.image_cover import ImageCover

PNG_FORMAT_NAME = "PNG"
DECIBEL_FACTOR = 10


def compare_images(original: ImageCover, stego: ImageCover) -> dict:
    """Metrics and an amplified difference map for two same-sized images."""
    _ensure_same_shape(original, stego)
    difference = _absolute_difference(original.samples(), stego.samples())
    mse = float(np.mean(difference.astype(np.float64) ** 2))
    return {
        "mse": round(mse, METRIC_DECIMALS),
        "psnr_db": _psnr(mse),
        "changed_values": int(np.count_nonzero(difference)),
        "total_values": int(difference.size),
        "max_difference": int(difference.max()),
        "difference_map_png": _encode_png(_amplified_difference_map(difference)),
    }


def _ensure_same_shape(original: ImageCover, stego: ImageCover) -> None:
    if original.samples().shape != stego.samples().shape:
        raise MediaFormatError("The original and stego images must have the same size and colour mode.")


def _absolute_difference(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    return np.abs(first.astype(np.int16) - second.astype(np.int16)).astype(np.uint8)


def _amplified_difference_map(difference: np.ndarray) -> np.ndarray:
    """Per-pixel max difference, stretched so the largest change is white."""
    per_pixel = difference.max(axis=2).astype(np.float64)
    peak = per_pixel.max()
    if peak == 0:
        return np.zeros(per_pixel.shape, dtype=np.uint8)
    return np.round(per_pixel / peak * MAX_PIXEL_VALUE).astype(np.uint8)


def _psnr(mse: float) -> float | None:
    if mse == 0:
        return None
    return round(DECIBEL_FACTOR * math.log10(MAX_PIXEL_VALUE**2 / mse), METRIC_DECIMALS)


def _encode_png(pixels: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    squeezed = pixels[:, :, 0] if pixels.ndim == 3 and pixels.shape[2] == 1 else pixels
    Image.fromarray(squeezed).save(buffer, format=PNG_FORMAT_NAME)
    return buffer.getvalue()
