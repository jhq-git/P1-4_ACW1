"""Protect endpoint: embed a signed payload into a cover object."""

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.presenters import present_protect_result
from app.api.schemas import ProtectResponse
from app.api.uploads import read_upload
from app.services.protector import ProtectRequest, protect

router = APIRouter(prefix="/api", tags=["protect"])


@router.post("/protect", response_model=ProtectResponse)
async def protect_media(
    cover: UploadFile = File(...),
    private_key: UploadFile = File(...),
    secret_key: str = Form(...),
    lsb_count: int = Form(...),
    sender_name: str = Form(""),
    note: str = Form(""),
) -> ProtectResponse:
    request = ProtectRequest(
        cover_bytes=await read_upload(cover, "Cover file"),
        private_key_pem=await read_upload(private_key, "Private key"),
        secret_key=secret_key,
        sender_name=sender_name,
        note=note,
        lsb_count=lsb_count,
    )
    result = await run_in_threadpool(protect, request)
    return present_protect_result(result, cover.filename)
