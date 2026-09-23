"""Key generation endpoint."""

from fastapi import APIRouter

from app.api.schemas import KeyPairResponse
from app.core.signing import generate_key_pair

router = APIRouter(prefix="/api", tags=["keys"])


@router.post("/keys", response_model=KeyPairResponse)
def create_key_pair() -> KeyPairResponse:
    """Generate a fresh Ed25519 key pair. Nothing is stored on the server."""
    key_pair = generate_key_pair()
    return KeyPairResponse(private_pem=key_pair.private_pem, public_pem=key_pair.public_pem)
