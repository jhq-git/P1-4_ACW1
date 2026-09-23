"""Ed25519 key generation, loading, signing and verification."""

from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.config import TEXT_ENCODING
from app.core.errors import KeyFormatError


@dataclass(frozen=True)
class KeyPairPem:
    private_pem: str
    public_pem: str


def generate_key_pair() -> KeyPairPem:
    """Create a new Ed25519 key pair encoded as PEM text."""
    private_key = Ed25519PrivateKey.generate()
    return KeyPairPem(
        private_pem=_private_key_to_pem(private_key),
        public_pem=_public_key_to_pem(private_key.public_key()),
    )


def load_private_key(pem: bytes) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(pem, password=None)
    except (ValueError, TypeError) as error:
        raise KeyFormatError("The private key file is not a valid unencrypted PEM key.") from error
    return _require_type(key, Ed25519PrivateKey, "private")


def load_public_key(pem: bytes) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(pem)
    except (ValueError, TypeError) as error:
        raise KeyFormatError("The public key file is not a valid PEM key.") from error
    return _require_type(key, Ed25519PublicKey, "public")


def sign(private_key: Ed25519PrivateKey, message: bytes) -> bytes:
    return private_key.sign(message)


def is_signature_valid(public_key: Ed25519PublicKey, message: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, message)
    except InvalidSignature:
        return False
    return True


def _private_key_to_pem(key: Ed25519PrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode(TEXT_ENCODING)


def _public_key_to_pem(key: Ed25519PublicKey) -> str:
    return key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode(TEXT_ENCODING)


def _require_type(key, expected_type, label: str):
    if not isinstance(key, expected_type):
        raise KeyFormatError(f"The {label} key must be an Ed25519 key.")
    return key
