from typing import Dict, List, Set
from fastapi.exceptions import HTTPException
from supabase import create_client, Client

from src.config import settings
from src.core.domain.interfaces import IFileService, ILogger


class SupabaseFileService(IFileService):
    # Maximum file size (5MB by default)
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

    # Allowed MIME types
    ALLOWED_MIME_TYPES: Set[str] = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    }

    def __init__(self, logger: ILogger):
        self.logger = logger
        self.supabase: Client = create_client(
            settings.supabase_url, settings.supabase_key
        )
        self.bucket_name = settings.supabase_bucket

    async def validate_file(self, file_type: str, file_size: int) -> bool:
        """
        Validate file type and size

        Args:
            file_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            True if file is valid, False otherwise
        """
        if file_type not in self.ALLOWED_MIME_TYPES:
            return False

        if file_size > self.MAX_FILE_SIZE_BYTES:
            return False

        return True

    async def generate_presigned_url(
        self, file_name: str, file_type: str, file_size: int
    ) -> Dict:
        """
        Generate a presigned URL for file upload

        Args:
            file_name: Original name of the file
            file_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            Dict containing the presigned URL and upload details
        """
        # Validate file first
        is_valid = await self.validate_file(file_type, file_size)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type or size exceeds the maximum allowed (10MB)",
            )

        try:
            # Generate a unique file path
            import uuid
            import os

            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Get presigned URL from Supabase
            response = self.supabase.storage.from_(
                self.bucket_name
            ).create_signed_upload_url(unique_filename)

            # Log the presigned URL generation
            self.logger.info(f"Generated presigned URL for file: {unique_filename}")

            return {
                "upload_url": response["signed_url"],
                "file_path": unique_filename,
                "expires_at": response["token"],
            }

        except Exception as e:
            self.logger.error(f"Error generating presigned URL: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Error generating presigned URL"
            )
