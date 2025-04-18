from abc import ABC, abstractmethod
from typing import Optional

from src.core.domain.models.file import File, SignedUrl


class IFileService(ABC):
    @abstractmethod
    async def generate_signed_url(self, file_path: str, user_id: str) -> SignedUrl:
        """
        Generate a signed URL for file upload

        Args:
            file_path: Path of the file in storage
            user_id: ID of the user requesting the signed URL

        Returns:
            SignedUrl containing the signed URL
        """
        pass

    @abstractmethod
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
            SignedUrl containing the signed URL
        """
        pass

    @abstractmethod
    async def generate_public_url(self, file_path: str, slug: str) -> SignedUrl:
        """
        Generate a public URL for a file

        Args:
            file_path: Path of the file in storage
            slug: ID of the profile

        Returns:
            SignedUrl containing the public URL
        """
        pass

    @abstractmethod
    async def copy_files_from_private_to_public(self, path: str) -> str:
        """
        Copy files from private to public bucket
        """
        pass

    @abstractmethod
    async def validate_file(self, file_type: str, file_size: int) -> bool:
        """
        Validate file type and size

        Args:
            file_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            True if file is valid, False otherwise
        """
        pass

    @abstractmethod
    async def download_remote_image(self, image_url: str) -> Optional[File]:
        """
        Download an image from a remote URL

        Args:
            image_url: URL of the remote image

        Returns:
            The file or None if failed
        """
        pass

    @abstractmethod
    async def upload_file(
        self,
        file: File,
        bucket_name: Optional[str] = None,
        path_prefix: str = "",
    ) -> str:
        """
        Upload a file to the file storage

        Args:
            file: The file to upload
            bucket_name: Optional bucket name to store the file
            path_prefix: Optional directory prefix to store the file (e.g. user ID)

        Returns:
            The path of the uploaded file or None if failed
        """
        pass

    @abstractmethod
    async def delete_public_files_from_folder(self, folder_path: str) -> None:
        """
        Delete files from the private bucket
        """
        pass

    @abstractmethod
    async def delete_files_from_folder(self, folder_path: str) -> None:
        """
        Delete files from the file storage

        Args:
            folder_path: Path of the folder to delete
        """
        pass
