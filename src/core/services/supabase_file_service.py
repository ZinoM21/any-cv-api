import mimetypes
import os
from typing import Optional
from urllib.parse import unquote, urlparse

import aiohttp
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from supabase import Client, ClientOptions, create_client

from src.config import Settings
from src.core.domain.interfaces import IFileService, ILogger, IProfileRepository
from src.core.domain.models.file import File, SignedUrl
from src.infrastructure.exceptions import (
    ApiErrorType,
    handle_exceptions,
)


class SupabaseFileService(IFileService):

    def __init__(
        self,
        logger: ILogger,
        settings: Settings,
        profile_repository: IProfileRepository,
    ):
        self.logger = logger
        self.settings = settings

        self.profile_repository = profile_repository
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
        self.private_bucket_name = self.settings.private_supabase_bucket
        self.public_bucket_name = self.settings.public_supabase_bucket

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

    def _get_all_files_from_folder_in_bucket(
        self, bucket_name: str, folder_path: str
    ) -> list[str]:
        """
        Get all files from a folder in a bucket
        """
        dict_array = self.supabase_service.storage.from_(bucket_name).list(folder_path)
        self.logger.debug(f"DICT ARRAY files in folder: {dict_array}")
        return [file["name"] for file in dict_array]

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
        if not file_path:
            raise RequestValidationError(
                errors=[
                    {
                        "loc": ["body", "file_path"],
                        "msg": "file_path cannot be empty",
                    }
                ]
            )

        if not self.verify_path_access(file_path, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ApiErrorType.Forbidden.value,
            )

        try:
            response = self.supabase_service.storage.from_(
                self.private_bucket_name
            ).create_signed_url(file_path, expires_in=self.settings.EXPIRES_IN_SECONDS)

            return SignedUrl(url=response["signedUrl"], path=file_path)

        except Exception as e:
            raise Exception(f"Error generating signed URL: {str(e)}")

    @handle_exceptions()
    async def generate_signed_upload_url(
        self,
        file_name: str,
        file_type: str,
        file_size: int,
        user_id: str,
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type or size exceeds the maximum allowed ({self.settings.MAX_FILE_SIZE_MB}MB)",
            )

        try:
            # Double check filename with correct extension & add user_id prefix
            filename, file_ext = os.path.splitext(file_name)
            filename = f"{filename or file_name}{file_ext or mimetypes.guess_extension(file_type) or ''}"

            if not self.verify_path_access(filename, user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ApiErrorType.Forbidden.value,
                )

            response = self.supabase_service.storage.from_(
                self.private_bucket_name
            ).create_signed_upload_url(filename)

            return SignedUrl(url=response["signedUrl"], path=response["path"])

        except Exception as e:
            raise Exception(f"Error generating signed URL: {str(e)}")

    @handle_exceptions()
    async def generate_public_url(self, file_path: str, slug: str) -> SignedUrl:
        """
        Generate a public URL for a file. Note: file has to be in a public bucket.

        Args:
            file_path: Path of the file in storage
            slug: ID of the profile

        Returns:
            SignedUrl containing the public URL
        """
        profile = self.profile_repository.find_published_by_slug(slug)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiErrorType.ResourceNotFound.value,
            )

        response = self.supabase_service.storage.from_(
            self.public_bucket_name
        ).get_public_url(file_path)

        return SignedUrl(url=response, path=file_path)

    @handle_exceptions()
    async def copy_files_from_private_to_public(self, path: str) -> str:
        """
        Copy files from private to public bucket
        """
        # Download file from private bucket
        try:
            file = self.supabase_service.storage.from_(
                self.private_bucket_name
            ).download(path)

            mimetype = mimetypes.guess_type(path)[0] or "application/octet-stream"

            file_download = File(
                data=file,
                filename=path,
                mimetype=mimetype,
            )

        except Exception as e:
            raise Exception(f"Error downloading from {self.private_bucket_name}: {e}")

        # Upload to public bucket
        return await self.upload_file(file_download, self.public_bucket_name)

    @handle_exceptions()
    async def download_remote_image(self, image_url: str) -> Optional[File]:
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

                    return File(
                        data=image_data,
                        filename=filename,
                        mimetype=mimetype,
                    )

        except Exception as e:
            raise Exception(f"Error downloading remote image: {str(e)}")

    @handle_exceptions()
    async def upload_file(
        self,
        file: File,
        bucket_name: Optional[str] = None,
        path_prefix: str = "",
    ) -> str:
        """
        Upload a file to Supabase storage

        Args:
            file: The file to upload with data in bytes, filename and mimetype
            path_prefix: Optional directory prefix to store the file (e.g. user ID)

        Returns:
            The file path in Supabase storage or None if failed
        """

        if not bucket_name:
            bucket_name = self.settings.private_supabase_bucket

        try:
            # Validate
            is_valid = await self.validate_file(file.mimetype, len(file.data))
            if not is_valid:
                raise Exception(
                    f"Invalid file type or size exceeds the maximum allowed ({self.settings.MAX_FILE_SIZE_MB}MB)",
                )

            # Double check filename with correct extension
            filename, file_ext = os.path.splitext(file.filename)
            filename = f"{filename or file.filename}{file_ext or mimetypes.guess_extension(file.mimetype) or ''}"

            # Add path prefix if provided
            filename = f"{path_prefix}/{filename}" if path_prefix else filename

            # Upload / Upsert
            self.supabase_service.storage.from_(bucket_name).upload(
                path=filename,
                file=file.data,
                file_options={
                    "content-type": file.mimetype,
                    "upsert": "true",
                },
            )

            return filename

        except Exception as e:
            raise Exception(f"Error uploading image: {str(e)}")

    @handle_exceptions()
    async def delete_private_files_from_folder(self, folder_path: str) -> None:
        """
        Delete files from the private bucket
        """
        private_files: list[str] = self._get_all_files_from_folder_in_bucket(
            self.settings.private_supabase_bucket, folder_path
        )
        if private_files:
            private_files_paths = [f"{folder_path}/{file}" for file in private_files]

            self.supabase_service.storage.from_(self.private_bucket_name).remove(
                private_files_paths
            )
            self.logger.debug("Files deleted from private bucket")

    @handle_exceptions()
    async def delete_public_files_from_folder(self, folder_path: str) -> None:
        """
        Delete files from the public bucket
        """
        public_files: list[str] = self._get_all_files_from_folder_in_bucket(
            self.settings.public_supabase_bucket, folder_path
        )
        if public_files:
            public_files_paths = [f"{folder_path}/{file}" for file in public_files]

            self.supabase_service.storage.from_(self.public_bucket_name).remove(
                public_files_paths
            )
            self.logger.debug("Files deleted from public bucket")

    @handle_exceptions()
    async def delete_files_from_folder(self, folder_path: str) -> None:
        """
        Delete files from the file storage

        Args:
            folder_path: Path of the folder to delete
        """
        await self.delete_private_files_from_folder(folder_path)
        await self.delete_public_files_from_folder(folder_path)
