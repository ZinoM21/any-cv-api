import mimetypes
import os
from typing import List, Optional
from urllib.parse import unquote, urlparse

import aiohttp
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from supabase import Client, ClientOptions, create_client

from src.config import Settings
from src.core.domain.dtos import File, SignedUrl
from src.core.domain.interfaces import IFileService, ILogger, IProfileRepository
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
            self.settings.SUPABASE_URL,
            self.settings.SUPABASE_PUBLISHABLE_KEY,
        )
        self.supabase_service: Client = create_client(
            self.settings.SUPABASE_URL,
            self.settings.SUPABASE_SECRET_KEY,
            # TODO: Remove this once authorization is implemented
            ClientOptions(
                headers={
                    "x-upsert": "true",
                }
            ),
        )
        self.private_bucket_name = self.settings.SUPABASE_PRIVATE_BUCKET
        self.public_bucket_name = self.settings.SUPABASE_PUBLIC_BUCKET

    async def _validate_file(self, file_type: str, file_size: int) -> bool:
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

    def _verify_path_access(self, path: str, user_id: str) -> bool:
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
        return [file["name"] for file in dict_array]

    async def _download_remote_file(self, url: str) -> Optional[File]:
        """
        Download a file from a remote URL

        Args:
            url: URL of the remote file

        Returns:
            The file download containing the data in bytes, filename and mimetype or None if failed
        """
        if not url:
            return None

        try:
            # Mimetype
            mimetype = mimetypes.guess_type(url)[0] or "image/jpeg"

            # Filename
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)
            base_filename = os.path.basename(path)

            filename, file_ext = os.path.splitext(base_filename)
            filename = f"{filename or base_filename}{file_ext or mimetypes.guess_extension(mimetype) or ''}"

            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.error(
                            f"Failed to download file from {url}: {response.status}"
                        )
                        return None

                    file_data = await response.read()

                    return File(
                        data=file_data,
                        filename=filename,
                        mimetype=mimetype,
                    )

        except Exception as e:
            raise Exception(f"Error downloading remote file: {str(e)}")

    async def _upload_file(
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
            bucket_name = self.settings.SUPABASE_PRIVATE_BUCKET

        try:
            # Validate
            is_valid = await self._validate_file(file.mimetype, len(file.data))
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

        if not self._verify_path_access(file_path, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ApiErrorType.Forbidden.value,
            )

        try:
            response = self.supabase_service.storage.from_(
                self.private_bucket_name
            ).create_signed_url(
                file_path, expires_in=self.settings.SIGNED_FILE_EXPIRES_IN_SECONDS
            )

            return SignedUrl(url=response["signedUrl"], path=file_path)

        except Exception as e:
            raise Exception(f"Error generating signed URL: {str(e)}")

    @handle_exceptions()
    async def generate_signed_urls(
        self, file_paths: List[str], user_id: str
    ) -> List[SignedUrl]:
        """
        Generate multiple signed URLs for files

        Args:
            file_paths: List of file paths in storage
            user_id: ID of the user requesting the signed URLs

        Returns:
            List of SignedUrl objects containing the signed URLs
        """
        if not file_paths:
            raise RequestValidationError(
                errors=[
                    {
                        "loc": ["body", "file_paths"],
                        "msg": "file_paths cannot be empty",
                    }
                ]
            )

        for file_path in file_paths:
            if not self._verify_path_access(file_path, user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ApiErrorType.Forbidden.value,
                )

        responses = self.supabase_service.storage.from_(
            self.private_bucket_name
        ).create_signed_urls(
            file_paths, expires_in=self.settings.SIGNED_FILE_EXPIRES_IN_SECONDS
        )

        return [
            SignedUrl(url=response["signedUrl"], path=response["path"])
            for response in responses
        ]

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
        is_valid = await self._validate_file(file_type, file_size)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type or size exceeds the maximum allowed ({self.settings.MAX_FILE_SIZE_MB}MB)",
            )

        try:
            # Double check filename with correct extension & add user_id prefix
            filename, file_ext = os.path.splitext(file_name)
            filename = f"{filename or file_name}{file_ext or mimetypes.guess_extension(file_type) or ''}"

            if not self._verify_path_access(filename, user_id):
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
        return await self._upload_file(file_download, self.public_bucket_name)

    async def download_and_store_file(
        self,
        url: str | None,
        path_prefix: str,
        filename: Optional[str] = None,
    ) -> str | None:
        """
        Download a file from a URL and upload it to file storage

        Args:
            url: The URL to download the file from
            path_prefix: used to create the path in storage
            filename: overwrites the filename of the downloaded file if provided

        Returns:
            The file path in storage or None
        """
        if not url:
            return None

        try:
            parsed_url = urlparse(url)

            if parsed_url.netloc in self.settings.LINKEDIN_MEDIA_DOMAINS:
                download = await self._download_remote_file(url)
                if download:
                    if filename:
                        download.filename = filename

                    uploaded_file_path = await self._upload_file(
                        file=download,
                        bucket_name=self.settings.SUPABASE_PRIVATE_BUCKET,
                        path_prefix=path_prefix,
                    )
                    return uploaded_file_path

        except Exception as e:
            self.logger.error(f"Error processing image URL: {str(e)}")
            return None

    @handle_exceptions()
    async def delete_private_files_from_folder(self, folder_path: str) -> None:
        """
        Delete files from the private bucket
        """
        private_files: list[str] = self._get_all_files_from_folder_in_bucket(
            self.settings.SUPABASE_PRIVATE_BUCKET, folder_path
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
            self.settings.SUPABASE_PUBLIC_BUCKET, folder_path
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
