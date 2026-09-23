"""Audio comparison visuals: downsampled waveforms, a zoom window and SNR."""

import math

import numpy as np

from app.config import METRIC_DECIMALS, WAVEFORM_BUCKET_COUNT, WAVEFORM_ZOOM_SAMPLE_COUNT
from app.core.errors import MediaFormatError
from app.media.audio_cover import AudioCover

DISPLAY_CHANNEL = 0
DECIBEL_FACTOR = 10


def compare_audio(original: AudioCover, stego: AudioCover) -> dict:
    """Metrics plus waveform data for the first channel of two same-length files."""
    _ensure_same_format(original, stego)
    original_channel = original.channel_samples(DISPLAY_CHANNEL).astype(np.int32)
    stego_channel = stego.channel_samples(DISPLAY_CHANNEL).astype(np.int32)
    difference = stego_channel - original_channel
    return {
        **_metrics(original.samples(), stego.samples()),
        "sample_rate": original.audio_format.sample_rate,
        "duration_seconds": original_channel.size / original.audio_format.sample_rate,
        "waveform": {
            "original": _min_max_envelope(original_channel),
            "stego": _min_max_envelope(stego_channel),
            "difference": _min_max_envelope(difference),
        },
        "zoom": _zoom_window(original_channel, stego_channel, difference),
    }


def _metrics(original: np.ndarray, stego: np.ndarray) -> dict:
    difference = stego.astype(np.int64) - original.astype(np.int64)
    return {
        "snr_db": _snr(original.astype(np.float64), difference.astype(np.float64)),
        "changed_samples": int(np.count_nonzero(difference)),
        "total_samples": int(difference.size),
        "max_difference": int(np.abs(difference).max()),
    }


def _ensure_same_format(original: AudioCover, stego: AudioCover) -> None:
    same_format = original.audio_format == stego.audio_format
    if not same_format or original.slot_count != stego.slot_count:
        raise MediaFormatError("The original and stego audio must have the same format and length.")


def _min_max_envelope(samples: np.ndarray) -> dict:
    """Split samples into buckets and keep each bucket's min and max."""
    bucket_count = min(WAVEFORM_BUCKET_COUNT, samples.size)
    buckets = np.array_split(samples, bucket_count)
    return {
        "min": [int(bucket.min()) for bucket in buckets],
        "max": [int(bucket.max()) for bucket in buckets],
    }


def _zoom_window(original: np.ndarray, stego: np.ndarray, difference: np.ndarray) -> dict:
    """Raw samples around the first changed sample (the payload start)."""
    changed = np.flatnonzero(difference)
    first_changed = int(changed[0]) if changed.size else 0
    start = max(0, first_changed - WAVEFORM_ZOOM_SAMPLE_COUNT // 4)
    end = min(original.size, start + WAVEFORM_ZOOM_SAMPLE_COUNT)
    return {
        "start_sample": start,
        "original": original[start:end].tolist(),
        "stego": stego[start:end].tolist(),
    }


def _snr(signal: np.ndarray, noise: np.ndarray) -> float | None:
    noise_power = float(np.sum(noise**2))
    signal_power = float(np.sum(signal**2))
    if noise_power == 0 or signal_power == 0:
        return None
    return round(DECIBEL_FACTOR * math.log10(signal_power / noise_power), METRIC_DECIMALS)
