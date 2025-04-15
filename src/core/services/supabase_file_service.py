import mimetypes
import os
from typing import Optional
from urllib.parse import unquote, urlparse

import aiohttp
from fastapi.exceptions import HTTPException
from supabase import Client, ClientOptions, create_client

from src.config import Settings
from src.core.domain.interfaces import IFileService, ILogger
from src.core.domain.models import ImageDownload, SignedUrl
from src.infrastructure.exceptions import handle_exceptions


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
            # TODO: Remove this once authorization is implemented
            ClientOptions(
                headers={
                    "x-upsert": "true",
                }
            ),
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

        if file_size > (self.settings.MAX_FILE_SIZE_MB * 1024 * 1024):
            return False

        return True

    def verify_path_access(self, path: str, user_id: str) -> bool:
        """
        Verify that the path is accessible by the user.
        Allow access only to the user's directory or files.
        Format of user paths should be: {user_id}/{filename}

        Args:
            path: Path to verify
            user_id: ID of the user attempting access

        Returns:
            True if access is allowed, False otherwise
        """
        return path.startswith(f"{user_id}/") or path == user_id

    @handle_exceptions()
    async def generate_signed_url(self, file_path: str, user_id: str) -> SignedUrl:
        """
        Generate a signed URL for file upload

        Args:
            file_path: Path of the file in storage
            user_id: ID of the user requesting the signed URL

        Returns:
            Dict containing the signed URL and other metadata
        """
        if not self.verify_path_access(file_path, user_id):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this file",
            )

        try:
            response = self.supabase_service.storage.from_(
                self.bucket_name
            ).create_signed_url(file_path, expires_in=self.settings.EXPIRES_IN_SECONDS)

            return SignedUrl(url=response["signedUrl"], path=file_path)

        except Exception as e:
            raise Exception(f"Error generating signed URL: {str(e)}")

    @handle_exceptions()
    async def generate_signed_upload_url(
        self, file_name: str, file_type: str, file_size: int, user_id: str
    ) -> SignedUrl:
        """
        Generate a signed URL for file upload

        Args:
            file_name: Original name of the file
            file_type: MIME type of the file
            file_size: Size of the file in bytes
            user_id: ID of the user requesting the signed URL

        Returns:
            Dict containing the signed URL and upload details
        """
        # Validate file first
        is_valid = await self.validate_file(file_type, file_size)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type or size exceeds the maximum allowed ({self.settings.MAX_FILE_SIZE_MB}MB)",
            )

        try:
            # Double check filename with correct extension & add user_id prefix
            filename, file_ext = os.path.splitext(file_name)
            filename = f"{user_id}/{filename or file_name}{file_ext or mimetypes.guess_extension(file_type) or ''}"

            if not self.verify_path_access(filename, user_id):
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to upload to this location",
                )

            response = self.supabase_service.storage.from_(
                self.bucket_name
            ).create_signed_upload_url(filename)

            return SignedUrl(url=response["signedUrl"], path=response["path"])

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
            # Mimetype
            mimetype = mimetypes.guess_type(image_url)[0] or "image/jpeg"

            # Filename
            parsed_url = urlparse(image_url)
            path = unquote(parsed_url.path)
            base_filename = os.path.basename(path)

            filename, file_ext = os.path.splitext(base_filename)
            filename = f"{filename or base_filename}{file_ext or mimetypes.guess_extension(mimetype) or ''}"

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
    async def upload_image(
        self, image_download: ImageDownload, path_prefix: str = ""
    ) -> Optional[str]:
        """
        Upload an image to Supabase storage

        Args:
            image_download: The image download with data in bytes, filename and mimetype
            path_prefix: Optional directory prefix to store the file (e.g. user ID)

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
                    f"Invalid file type or size exceeds the maximum allowed ({self.settings.MAX_FILE_SIZE_MB}MB)",
                )

            # Double check filename with correct extension
            mimetype = image_download.mimetype
            filename, file_ext = os.path.splitext(image_download.filename)
            filename = f"{filename or image_download.filename}{file_ext or mimetypes.guess_extension(mimetype) or ''}"

            # Add path prefix if provided
            filename = f"{path_prefix}/{filename}" if path_prefix else filename

            # Upload / Upsert
            self.supabase_service.storage.from_(self.bucket_name).upload(
                path=filename,
                file=image_download.data,
                file_options={
                    "content-type": mimetype,
                    "upsert": "true",
                },
            )

            return filename

        except Exception as e:
            raise Exception(f"Error uploading remote image: {str(e)}")
