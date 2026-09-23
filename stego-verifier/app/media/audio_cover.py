"""16-bit PCM WAV cover objects (mono or stereo).

Each interleaved sample is one slot. Samples are handled as unsigned 16-bit
values for bit operations and stored as signed little-endian on disk.
"""

import io
import wave
from dataclasses import dataclass

import numpy as np

from app.config import (
    AUDIO_EXTENSION,
    AUDIO_MIME_TYPE,
    BITS_PER_BYTE,
    SUPPORTED_AUDIO_CHANNEL_COUNTS,
    SUPPORTED_AUDIO_SAMPLE_WIDTH_BYTES,
    WAV_RIFF_TAG,
    WAV_WAVE_TAG,
    WAV_WAVE_TAG_OFFSET,
)
from app.core.errors import MediaFormatError
from app.core.payload import MediaType
from app.media.base import CoverMedia

PCM_SAMPLE_DTYPE = np.dtype("<i2")
SLOT_DTYPE = np.dtype("<u2")
UNCOMPRESSED_TYPE = "NONE"
CHANNEL_NAMES = {1: "mono", 2: "stereo"}
BITS_PER_SAMPLE = SUPPORTED_AUDIO_SAMPLE_WIDTH_BYTES * BITS_PER_BYTE


@dataclass(frozen=True)
class AudioFormat:
    channel_count: int
    sample_rate: int


class AudioCover(CoverMedia):
    media_type = MediaType.AUDIO
    mime_type = AUDIO_MIME_TYPE
    file_extension = AUDIO_EXTENSION

    def __init__(self, samples: np.ndarray, audio_format: AudioFormat):
        self._samples = samples
        self._format = audio_format

    @classmethod
    def from_bytes(cls, data: bytes) -> "AudioCover":
        _ensure_wav_tags(data)
        frames, audio_format = _read_pcm_frames(data)
        samples = np.frombuffer(frames, dtype=PCM_SAMPLE_DTYPE)
        whole_frame_count = samples.size - samples.size % audio_format.channel_count
        return cls(samples[:whole_frame_count].copy(), audio_format)

    @property
    def audio_format(self) -> AudioFormat:
        return self._format

    @property
    def slot_count(self) -> int:
        return self._samples.size

    def read_slots(self) -> np.ndarray:
        return self._samples.view(SLOT_DTYPE).copy()

    def with_slots(self, slots: np.ndarray) -> "AudioCover":
        return AudioCover(slots.astype(SLOT_DTYPE).view(PCM_SAMPLE_DTYPE), self._format)

    def canonical_bytes(self) -> bytes:
        return self._samples.astype(PCM_SAMPLE_DTYPE).tobytes()

    def samples(self) -> np.ndarray:
        return self._samples

    def channel_samples(self, channel_index: int) -> np.ndarray:
        return self._samples[channel_index :: self._format.channel_count]

    def encode(self) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as writer:
            writer.setnchannels(self._format.channel_count)
            writer.setsampwidth(SUPPORTED_AUDIO_SAMPLE_WIDTH_BYTES)
            writer.setframerate(self._format.sample_rate)
            writer.writeframes(self.canonical_bytes())
        return buffer.getvalue()

    def describe(self) -> str:
        channels = CHANNEL_NAMES[self._format.channel_count]
        duration = self._samples.size / self._format.channel_count / self._format.sample_rate
        return f"{self._format.sample_rate:,} Hz · {BITS_PER_SAMPLE}-bit · {channels} · {duration:.2f} s"


def _ensure_wav_tags(data: bytes) -> None:
    wave_tag_end = WAV_WAVE_TAG_OFFSET + len(WAV_WAVE_TAG)
    if not data.startswith(WAV_RIFF_TAG) or data[WAV_WAVE_TAG_OFFSET:wave_tag_end] != WAV_WAVE_TAG:
        raise MediaFormatError("The file is not a valid WAV file.")


def _read_pcm_frames(data: bytes) -> tuple[bytes, AudioFormat]:
    try:
        with wave.open(io.BytesIO(data), "rb") as reader:
            _ensure_supported_params(reader)
            frames = reader.readframes(reader.getnframes())
            return frames, AudioFormat(reader.getnchannels(), reader.getframerate())
    except (wave.Error, EOFError) as error:
        raise MediaFormatError(f"WAV file cannot be read as 16-bit PCM: {error}") from error


def _ensure_supported_params(reader: wave.Wave_read) -> None:
    if reader.getcomptype() != UNCOMPRESSED_TYPE:
        raise MediaFormatError("Compressed WAV files are not supported.")
    if reader.getsampwidth() != SUPPORTED_AUDIO_SAMPLE_WIDTH_BYTES:
        raise MediaFormatError(f"{reader.getsampwidth() * BITS_PER_BYTE}-bit WAV is not supported; use 16-bit PCM.")
    if reader.getnchannels() not in SUPPORTED_AUDIO_CHANNEL_COUNTS:
        raise MediaFormatError("Only mono and stereo WAV files are supported.")
