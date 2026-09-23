"""Shared fixtures: synthetic covers, keys and helpers."""

import io
import wave

import numpy as np
import pytest
from PIL import Image

from app.core.signing import generate_key_pair
from app.services.protector import ProtectRequest, protect

SECRET_KEY = "correct horse battery staple"
SAMPLE_RATE = 8000
AUDIO_SECONDS = 1
IMAGE_SIZE = 64
RANDOM_SEED = 2005


@pytest.fixture(scope="session")
def rng():
    return np.random.default_rng(RANDOM_SEED)


@pytest.fixture(scope="session")
def key_pair():
    return generate_key_pair()


@pytest.fixture(scope="session")
def other_key_pair():
    return generate_key_pair()


def make_png(pixels: np.ndarray, **save_options) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG", **save_options)
    return buffer.getvalue()


def make_wav(samples: np.ndarray, channels: int, sample_width: int = 2, sample_rate: int = SAMPLE_RATE) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(sample_width)
        writer.setframerate(sample_rate)
        writer.writeframes(samples.tobytes())
    return buffer.getvalue()


@pytest.fixture(scope="session")
def covers(rng) -> dict[str, bytes]:
    shape = (IMAGE_SIZE, IMAGE_SIZE)
    tone = (np.sin(np.arange(SAMPLE_RATE * AUDIO_SECONDS * 2) / 7) * 9000).astype("<i2")
    return {
        "png_l": make_png(rng.integers(0, 256, shape, dtype=np.uint8)),
        "png_la": make_png(rng.integers(0, 256, (*shape, 2), dtype=np.uint8)),
        "png_rgb": make_png(rng.integers(0, 256, (*shape, 3), dtype=np.uint8)),
        "png_rgba": make_png(rng.integers(0, 256, (*shape, 4), dtype=np.uint8)),
        "wav_mono": make_wav(tone[: SAMPLE_RATE * AUDIO_SECONDS], channels=1),
        "wav_stereo": make_wav(tone, channels=2),
    }


def protect_cover(cover: bytes, key_pair, lsb_count: int = 1, note: str = "meet at noon") -> bytes:
    request = ProtectRequest(
        cover_bytes=cover,
        private_key_pem=key_pair.private_pem.encode(),
        secret_key=SECRET_KEY,
        sender_name="Alice",
        note=note,
        lsb_count=lsb_count,
    )
    return protect(request).stego.encode()
