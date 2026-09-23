"""Verify endpoint: extract the payload and return a verdict."""

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.presenters import present_verification
from app.api.schemas import VerifyResponse
from app.api.uploads import read_upload
from app.services.verifier import VerifyRequest, verify

router = APIRouter(prefix="/api", tags=["verify"])


@router.post("/verify", response_model=VerifyResponse)
async def verify_media(
    stego: UploadFile = File(...),
    public_key: UploadFile = File(...),
    secret_key: str = Form(""),
) -> VerifyResponse:
    request = VerifyRequest(
        stego_bytes=await read_upload(stego, "Stego file"),
        public_key_pem=await read_upload(public_key, "Public key"),
        secret_key=secret_key,
    )
    report = await run_in_threadpool(verify, request)
    return present_verification(report)
