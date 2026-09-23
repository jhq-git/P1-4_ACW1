"""Common interface for cover objects (images and audio)."""

from abc import ABC, abstractmethod

import numpy as np

from app.core.payload import MediaType


class CoverMedia(ABC):
    """A loaded cover or stego object exposing its embeddable slots."""

    media_type: MediaType
    mime_type: str
    file_extension: str

    @property
    @abstractmethod
    def slot_count(self) -> int:
        """Number of embeddable slots (N)."""

    @abstractmethod
    def read_slots(self) -> np.ndarray:
        """Return a flat, unsigned copy of all embeddable slot values."""

    @abstractmethod
    def with_slots(self, slots: np.ndarray) -> "CoverMedia":
        """Return a new cover with the embeddable slots replaced."""

    @abstractmethod
    def canonical_bytes(self) -> bytes:
        """All sample data in a fixed layout, used as hash input."""

    @abstractmethod
    def samples(self) -> np.ndarray:
        """Full sample array (including non-embeddable channels) for analysis."""

    @abstractmethod
    def encode(self) -> bytes:
        """Serialize to a PNG or WAV file."""

    @abstractmethod
    def describe(self) -> str:
        """Short human-readable description, e.g. '512x512 RGB'."""
