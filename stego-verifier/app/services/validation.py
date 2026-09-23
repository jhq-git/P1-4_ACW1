"""Validation of user-supplied Protect and Verify inputs."""

from app.config import MAX_LSB_COUNT, MIN_LSB_COUNT, MIN_SECRET_KEY_LENGTH
from app.core.errors import InputValidationError


def validate_lsb_count(lsb_count: int) -> None:
    if not MIN_LSB_COUNT <= lsb_count <= MAX_LSB_COUNT:
        raise InputValidationError(f"Number of LSBs must be between {MIN_LSB_COUNT} and {MAX_LSB_COUNT}.")


def validate_new_secret_key(secret_key: str) -> None:
    """Secret keys used for protecting must meet the minimum length."""
    if len(secret_key) < MIN_SECRET_KEY_LENGTH:
        raise InputValidationError(f"Secret key must be at least {MIN_SECRET_KEY_LENGTH} characters.")


def validate_secret_key_present(secret_key: str) -> None:
    if not secret_key:
        raise InputValidationError("A secret key is required.")
