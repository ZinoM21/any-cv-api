from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.decorators import handle_exceptions
from src.deps import FileServiceDep, LoggerDep


class FileValidationRequest(BaseModel):
    file_name: str
    file_type: str
    file_size: int


file_controller_v1 = APIRouter(prefix="/v1/files")


@file_controller_v1.get("/healthz")
async def healthz():
    return JSONResponse(content={"status": "ok"})


@file_controller_v1.post("/validate")
@handle_exceptions()
async def validate_file(
    file_data: FileValidationRequest, file_service: FileServiceDep, logger: LoggerDep
):
    """Validate if a file type and size are acceptable"""
    is_valid = await file_service.validate_file(
        file_data.file_type, file_data.file_size
    )

    return JSONResponse(content={"valid": is_valid})


@file_controller_v1.post("/presigned-url")
@handle_exceptions()
async def get_presigned_url(
    file_data: FileValidationRequest, file_service: FileServiceDep, logger: LoggerDep
):
    """Get a presigned URL for file upload"""
    presigned_data = await file_service.generate_presigned_url(
        file_data.file_name, file_data.file_type, file_data.file_size
    )

    return JSONResponse(content=presigned_data)
