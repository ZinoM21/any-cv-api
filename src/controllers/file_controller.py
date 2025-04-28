from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.domain.dtos import SignedUrl
from src.deps import CurrentUserDep, FileServiceDep
from src.infrastructure.exceptions import handle_exceptions


class SignedUploadUrlRequest(BaseModel):
    file_name: str
    file_type: str
    file_size: int


class SignedUrlRequest(BaseModel):
    file_path: str


class SignedUrlsRequest(BaseModel):
    file_paths: List[str]


file_controller_v1 = APIRouter(prefix="/v1/files")


@file_controller_v1.get("/healthz")
async def healthz():
    return JSONResponse(content={"status": "ok"})


@file_controller_v1.post("/signed-upload-url", response_model=SignedUrl)
@handle_exceptions()
async def get_signed_upload_url(
    file_data: SignedUploadUrlRequest,
    file_service: FileServiceDep,
    current_user: CurrentUserDep,
):
    """Get a signed URL for file upload for authenticated users"""
    return await file_service.generate_signed_upload_url(
        file_name=file_data.file_name,
        file_type=file_data.file_type,
        file_size=file_data.file_size,
        user_id=str(current_user.id),
    )


@file_controller_v1.post("/signed-url", response_model=SignedUrl)
@handle_exceptions()
async def get_signed_url(
    request: SignedUrlRequest,
    file_service: FileServiceDep,
    current_user: CurrentUserDep,
):
    """Get a signed URL for accessing files for authenticated users"""
    return await file_service.generate_signed_url(
        file_path=request.file_path,
        user_id=str(current_user.id),
    )


@file_controller_v1.post("/signed-urls", response_model=List[SignedUrl])
@handle_exceptions()
async def get_signed_urls(
    request: SignedUrlsRequest,
    file_service: FileServiceDep,
    current_user: CurrentUserDep,
):
    """Get multiple signed URLs for accessing files for authenticated users"""
    return await file_service.generate_signed_urls(
        file_paths=request.file_paths,
        user_id=str(current_user.id),
    )


@file_controller_v1.post("/public/{slug}", response_model=SignedUrl)
@handle_exceptions()
async def get_public_url(
    slug: str,
    request: SignedUrlRequest,
    file_service: FileServiceDep,
):
    """Get a public URL for accessing files without authentication"""
    return await file_service.generate_public_url(
        file_path=request.file_path,
        slug=slug,
    )
