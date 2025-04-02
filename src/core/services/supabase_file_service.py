import mimetypes
import os
import uuid
from typing import Optional
from urllib.parse import unquote, urlparse

import aiohttp
from fastapi.exceptions import HTTPException
from supabase import Client, create_client

from src.config import Settings
from src.core.domain.interfaces import IFileService, ILogger
from src.core.domain.models.file import ImageDownload, SignedUrl
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class SupabaseFileService(IFileService):

    def __init__(self, logger: ILogger, settings: Settings):
        self.logger = logger
        self.settings = settings

        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_publishable_key,
        )
        self.supabase_service: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_secret_key,
        )
        self.bucket_name = self.settings.supabase_bucket

    async def validate_file(self, file_type: str, file_size: int) -> bool:
        """
        Validate file type and size

        Args:
            file_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            True if file of allowed type and size, False otherwise
        """
        if file_type not in self.settings.ALLOWED_MIME_TYPES:
            return False

        if file_size > self.settings.MAX_FILE_SIZE_BYTES:
            return False

        return True

    @handle_exceptions()
    async def generate_signed_url(self, file_path: str) -> SignedUrl:
        """
        Generate a signed URL for file upload

        Args:
            file_path: Path of the file in storage

        Returns:
            Dict containing the signed URL and other metadata
        """
        try:
            # Get signed URL from Supabase
            response = self.supabase_service.storage.from_(
                self.bucket_name
            ).create_signed_url(file_path, expires_in=self.settings.EXPIRES_IN_SECONDS)

            return SignedUrl(signed_url=response["signedUrl"])

        except Exception as e:
            raise Exception(f"Error generating signed URL: {str(e)}")

    @handle_exceptions()
    async def generate_signed_upload_url(
        self, file_name: str, file_type: str, file_size: int
    ) -> SignedUrl:
        """
        Generate a signed URL for file upload

        Args:
            file_name: Original name of the file
            file_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            Dict containing the signed URL and upload details
        """
        # Validate file first
        is_valid = await self.validate_file(file_type, file_size)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type or size exceeds the maximum allowed (10MB)",
            )

        try:
            # Filename
            filename, file_ext = os.path.splitext(file_name)
            if not file_ext:
                file_ext = ".jpg"
            filename = f"{filename or file_name}{file_ext}"

            response = self.supabase_service.storage.from_(
                self.bucket_name
            ).create_signed_upload_url(filename)

            return SignedUrl(signed_url=response["signedUrl"])

        except Exception as e:
            raise Exception(f"Error generating signed URL: {str(e)}")

    @handle_exceptions()
    async def download_remote_image(self, image_url: str) -> Optional[ImageDownload]:
        """
        Download an image from a remote URL

        Args:
            image_url: URL of the remote image

        Returns:
            The image download containing the data in bytes, filename and mimetype or None if failed
        """
        if not image_url:
            return None

        try:
            # Filename
            parsed_url = urlparse(image_url)
            path = unquote(parsed_url.path)
            base_filename = os.path.basename(path)

            filename, file_ext = os.path.splitext(base_filename)
            if not file_ext:
                file_ext = ".jpg"
            filename = f"{filename or base_filename}{file_ext}"

            # Mimetype
            mimetype = mimetypes.guess_type(image_url)[0] or "image/jpeg"

            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        self.logger.error(
                            f"Failed to download image from {image_url}: {response.status}"
                        )
                        return None

                    image_data = await response.read()

                    return ImageDownload(
                        data=image_data,
                        filename=filename,
                        mimetype=mimetype,
                    )

        except Exception as e:
            raise Exception(f"Error downloading remote image: {str(e)}")

    @handle_exceptions()
    async def upload_image(self, image_download: ImageDownload) -> Optional[str]:
        """
        Upload an image to Supabase storage

        Args:
            image_download: The image download with data in bytes, filename and mimetype

        Returns:
            The file path in Supabase storage or None if failed
        """

        try:
            # Validate
            is_valid = await self.validate_file(
                image_download.mimetype, len(image_download.data)
            )
            if not is_valid:
                raise Exception(
                    "Invalid file type or size exceeds the maximum allowed (10MB)",
                )

            # Upload / Upsert
            self.supabase_service.storage.from_(self.bucket_name).upload(
                path=image_download.filename,
                file=image_download.data,
                file_options={
                    "content-type": image_download.mimetype,
                    "upsert": "true",
                },
            )

            return image_download.filename

        except Exception as e:
            raise Exception(f"Error uploading remote image: {str(e)}")

