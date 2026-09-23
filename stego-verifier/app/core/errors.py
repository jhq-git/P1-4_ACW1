"""Domain exceptions raised by the core, media and service layers."""


class StegoError(Exception):
    """Base class for all expected, user-facing errors."""


class InputValidationError(StegoError):
    """A user-supplied value (secret key, sender, note, LSB count) is invalid."""


class MediaFormatError(StegoError):
    """The file is not a supported PNG or WAV cover object."""


class KeyFormatError(StegoError):
    """A supplied PEM key cannot be parsed or is not an Ed25519 key."""


class InsufficientCapacityError(StegoError):
    """The cover object does not have enough slots for the payload."""


class PayloadMissingError(StegoError):
    """No valid magic value was found at the derived start location."""


class HeaderInvalidError(StegoError):
    """The header was found but its fields are out of range."""


class PayloadFormatError(StegoError):
    """The body bytes cannot be parsed into payload fields."""


class SignatureInvalidError(StegoError):
    """The Ed25519 signature does not match the payload content."""


class HashMismatchError(StegoError):
    """The recomputed media hash differs from the signed hash."""
