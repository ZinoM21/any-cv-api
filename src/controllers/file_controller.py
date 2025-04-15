from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.domain.models import SignedUrl
from src.deps import CurrentUserDep, FileServiceDep
from src.infrastructure.exceptions import handle_exceptions


class SignedUploadUrlRequest(BaseModel):
    file_name: str
    file_type: str
    file_size: int


class SignedUrlRequest(BaseModel):
    file_path: str


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
