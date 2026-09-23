"""PNG cover objects.

Supported: 8-bit L, LA, RGB, RGBA. Palette images become RGB (or RGBA when
they have transparency) and 1-bit images become L. Alpha is hashed but never
used for embedding.
"""

import io

import numpy as np
from PIL import Image, UnidentifiedImageError

from app.config import IMAGE_EXTENSION, IMAGE_MIME_TYPE, PNG_SIGNATURE
from app.core.errors import MediaFormatError
from app.core.payload import MediaType
from app.media.base import CoverMedia

PNG_FORMAT_NAME = "PNG"
PNG_IHDR_BIT_DEPTH_OFFSET = 24
MAX_SUPPORTED_BIT_DEPTH = 8
TRANSPARENCY_INFO_KEY = "transparency"

EMBEDDABLE_CHANNELS_BY_MODE = {
    "L": (0,),
    "LA": (0,),
    "RGB": (0, 1, 2),
    "RGBA": (0, 1, 2),
}
MODE_CONVERSIONS = {"1": "L"}


class ImageCover(CoverMedia):
    media_type = MediaType.IMAGE
    mime_type = IMAGE_MIME_TYPE
    file_extension = IMAGE_EXTENSION

    def __init__(self, pixels: np.ndarray, mode: str):
        self._pixels = pixels
        self._mode = mode
        self._channels = EMBEDDABLE_CHANNELS_BY_MODE[mode]

    @classmethod
    def from_bytes(cls, data: bytes) -> "ImageCover":
        _ensure_png_bit_depth(data)
        image = _normalize_mode(_open_png(data))
        pixels = np.array(image, dtype=np.uint8)
        return cls(_ensure_channel_axis(pixels), image.mode)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def slot_count(self) -> int:
        height, width, _ = self._pixels.shape
        return height * width * len(self._channels)

    def read_slots(self) -> np.ndarray:
        return self._pixels[:, :, self._channels].reshape(-1).copy()

    def with_slots(self, slots: np.ndarray) -> "ImageCover":
        height, width, _ = self._pixels.shape
        pixels = self._pixels.copy()
        pixels[:, :, self._channels] = slots.reshape(height, width, len(self._channels))
        return ImageCover(pixels, self._mode)

    def canonical_bytes(self) -> bytes:
        return self._pixels.tobytes()

    def samples(self) -> np.ndarray:
        return self._pixels

    def encode(self) -> bytes:
        buffer = io.BytesIO()
        Image.fromarray(_drop_single_channel_axis(self._pixels)).save(buffer, format=PNG_FORMAT_NAME)
        return buffer.getvalue()

    def describe(self) -> str:
        height, width, _ = self._pixels.shape
        return f"{width}×{height} PNG · {self._mode}"


def _open_png(data: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise MediaFormatError("The PNG file is corrupt or cannot be decoded.") from error
    if image.format != PNG_FORMAT_NAME:
        raise MediaFormatError("Only PNG images are supported.")
    return image


def _ensure_png_bit_depth(data: bytes) -> None:
    if not data.startswith(PNG_SIGNATURE) or len(data) <= PNG_IHDR_BIT_DEPTH_OFFSET:
        raise MediaFormatError("The file is not a valid PNG image.")
    bit_depth = data[PNG_IHDR_BIT_DEPTH_OFFSET]
    if bit_depth > MAX_SUPPORTED_BIT_DEPTH:
        raise MediaFormatError(f"{bit_depth}-bit PNG images are not supported; use 8-bit.")


def _normalize_mode(image: Image.Image) -> Image.Image:
    if image.mode == "P":
        has_transparency = TRANSPARENCY_INFO_KEY in image.info
        return image.convert("RGBA" if has_transparency else "RGB")
    if image.mode in MODE_CONVERSIONS:
        return image.convert(MODE_CONVERSIONS[image.mode])
    if image.mode not in EMBEDDABLE_CHANNELS_BY_MODE:
        raise MediaFormatError(f"PNG colour mode '{image.mode}' is not supported.")
    return image


def _ensure_channel_axis(pixels: np.ndarray) -> np.ndarray:
    return pixels[:, :, np.newaxis] if pixels.ndim == 2 else pixels


def _drop_single_channel_axis(pixels: np.ndarray) -> np.ndarray:
    return pixels[:, :, 0] if pixels.shape[2] == 1 else pixels
