"""End-to-end Protect -> tamper -> Verify scenarios for every verdict."""

import io

import numpy as np
import pytest
from PIL import Image

from app.core.errors import InputValidationError, InsufficientCapacityError, MediaFormatError
from app.core.layout import plan_layout
from app.core.location import derive_location_key, derive_start_slot
from app.core.payload import compute_body_length
from app.media.loader import load_cover
from app.services.verdicts import Verdict
from app.services.verifier import VerifyRequest, verify
from tests.conftest import SECRET_KEY, make_png, make_wav, protect_cover

ALL_COVERS = ["png_l", "png_la", "png_rgb", "png_rgba", "wav_mono", "wav_stereo"]
LSB_COUNTS = [1, 2, 4, 8]
NOTE = "meet at noon"
SENDER = "Alice"


def run_verify(stego: bytes, key_pair, secret_key: str = SECRET_KEY):
    return verify(VerifyRequest(stego, key_pair.public_pem.encode(), secret_key))


def payload_layout(stego: bytes, lsb_count: int):
    cover = load_cover(stego)
    key = derive_location_key(SECRET_KEY)
    start = derive_start_slot(key, cover.slot_count)
    return cover, plan_layout(start, cover.slot_count, lsb_count, compute_body_length(SENDER, NOTE))


def flip_slot_bit(stego: bytes, slot_index: int, bit: int = 0) -> bytes:
    cover = load_cover(stego)
    slots = cover.read_slots()
    slots[slot_index] ^= slots.dtype.type(1 << bit)
    return cover.with_slots(slots).encode()


def first_slot_outside_payload(layout, slot_count: int) -> int:
    used = set(layout.header_slots.tolist()) | set(layout.body_slots.tolist())
    return next(index for index in range(slot_count) if index not in used)


# --- Authentic ---------------------------------------------------------------

@pytest.mark.parametrize("cover_name", ALL_COVERS)
@pytest.mark.parametrize("lsb_count", LSB_COUNTS)
def test_round_trip_is_authentic(covers, key_pair, cover_name, lsb_count):
    stego = protect_cover(covers[cover_name], key_pair, lsb_count)
    report = run_verify(stego, key_pair)
    assert report.verdict is Verdict.AUTHENTIC
    assert report.fields.note == NOTE
    assert report.lsb_count == lsb_count


def test_lossless_png_resave_is_authentic(covers, key_pair):
    stego = protect_cover(covers["png_rgb"], key_pair)
    resaved = make_png(np.array(Image.open(io.BytesIO(stego))), compress_level=9)
    assert run_verify(resaved, key_pair).verdict is Verdict.AUTHENTIC


def test_sample_rate_header_edit_is_not_detected(covers, key_pair):
    """Known limitation: format parameters are not hashed."""
    stego = protect_cover(covers["wav_mono"], key_pair)
    samples = load_cover(stego).samples()
    edited = make_wav(samples, channels=1, sample_rate=16000)
    assert run_verify(edited, key_pair).verdict is Verdict.AUTHENTIC


# --- Tampered ----------------------------------------------------------------

@pytest.mark.parametrize("cover_name", ["png_rgb", "wav_mono"])
def test_edit_outside_payload_is_tampered(covers, key_pair, cover_name):
    stego = protect_cover(covers[cover_name], key_pair)
    cover, layout = payload_layout(stego, lsb_count=1)
    target = first_slot_outside_payload(layout, cover.slot_count)
    tampered = flip_slot_bit(stego, target, bit=6)
    assert run_verify(tampered, key_pair).verdict is Verdict.TAMPERED


@pytest.mark.parametrize("cover_name", ["png_rgb", "wav_stereo"])
def test_lsb_flip_outside_payload_is_tampered(covers, key_pair, cover_name):
    stego = protect_cover(covers[cover_name], key_pair)
    cover, layout = payload_layout(stego, lsb_count=1)
    tampered = flip_slot_bit(stego, first_slot_outside_payload(layout, cover.slot_count))
    assert run_verify(tampered, key_pair).verdict is Verdict.TAMPERED


def test_alpha_channel_edit_is_tampered(covers, key_pair):
    stego = protect_cover(covers["png_rgba"], key_pair)
    pixels = np.array(Image.open(io.BytesIO(stego)))
    pixels[0, 0, 3] ^= 1
    assert run_verify(make_png(pixels), key_pair).verdict is Verdict.TAMPERED


# --- Signature Invalid -------------------------------------------------------

@pytest.mark.parametrize("cover_name", ["png_l", "wav_mono"])
def test_payload_bit_flip_is_signature_invalid(covers, key_pair, cover_name):
    stego = protect_cover(covers[cover_name], key_pair)
    _, layout = payload_layout(stego, lsb_count=1)
    tampered = flip_slot_bit(stego, int(layout.body_slots[40]))
    report = run_verify(tampered, key_pair)
    assert report.verdict is Verdict.SIGNATURE_INVALID
    assert not report.fields_verified


def test_wrong_public_key_is_signature_invalid(covers, key_pair, other_key_pair):
    stego = protect_cover(covers["png_rgb"], key_pair)
    assert run_verify(stego, other_key_pair).verdict is Verdict.SIGNATURE_INVALID


# --- Payload Missing ---------------------------------------------------------

def test_wrong_secret_key_is_payload_missing(covers, key_pair):
    stego = protect_cover(covers["png_rgb"], key_pair)
    assert run_verify(stego, key_pair, "wrong secret key!!").verdict is Verdict.PAYLOAD_MISSING


@pytest.mark.parametrize("cover_name", ALL_COVERS)
def test_unprotected_cover_is_payload_missing(covers, key_pair, cover_name):
    assert run_verify(covers[cover_name], key_pair).verdict is Verdict.PAYLOAD_MISSING


def test_cropped_image_is_payload_missing(covers, key_pair):
    stego = protect_cover(covers["png_rgb"], key_pair)
    pixels = np.array(Image.open(io.BytesIO(stego)))
    assert run_verify(make_png(pixels[1:, :, :]), key_pair).verdict is Verdict.PAYLOAD_MISSING


# --- Cannot Verify -----------------------------------------------------------

@pytest.mark.parametrize(
    "data",
    [b"", b"not a media file", b"\x89PNG\r\n\x1a\ntruncated", b"\xff\xd8\xff\xe0 jpeg-ish"],
)
def test_unreadable_input_is_cannot_verify(key_pair, data):
    assert run_verify(data, key_pair).verdict is Verdict.CANNOT_VERIFY


def test_eight_bit_wav_is_cannot_verify(key_pair):
    samples = np.full(4000, 128, dtype=np.uint8)
    assert run_verify(make_wav(samples, channels=1, sample_width=1), key_pair).verdict is Verdict.CANNOT_VERIFY


def test_sixteen_bit_png_is_cannot_verify(key_pair):
    pixels = np.zeros((16, 16), dtype=np.uint16)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    assert run_verify(buffer.getvalue(), key_pair).verdict is Verdict.CANNOT_VERIFY


def test_invalid_public_key_is_cannot_verify(covers, key_pair):
    stego = protect_cover(covers["png_rgb"], key_pair)
    report = verify(VerifyRequest(stego, b"not a key", SECRET_KEY))
    assert report.verdict is Verdict.CANNOT_VERIFY


# --- Protect input validation ------------------------------------------------

def test_cover_too_small_is_rejected(key_pair):
    tiny = make_png(np.zeros((8, 8), dtype=np.uint8))
    with pytest.raises(InsufficientCapacityError):
        protect_cover(tiny, key_pair)


def test_short_secret_key_is_rejected(covers, key_pair):
    from app.services.protector import ProtectRequest, protect

    request = ProtectRequest(covers["png_rgb"], key_pair.private_pem.encode(), "short", "", "", 1)
    with pytest.raises(InputValidationError):
        protect(request)


def test_palette_and_one_bit_pngs_are_supported(key_pair, rng):
    palette = Image.fromarray(rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)).convert("P")
    one_bit = Image.fromarray(rng.integers(0, 2, (96, 96), dtype=np.uint8) * 255).convert("1")
    for image in (palette, one_bit):
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        stego = protect_cover(buffer.getvalue(), key_pair)
        assert run_verify(stego, key_pair).verdict is Verdict.AUTHENTIC


def test_jpeg_is_rejected_on_load():
    with pytest.raises(MediaFormatError):
        load_cover(b"\xff\xd8\xff\xe0")
