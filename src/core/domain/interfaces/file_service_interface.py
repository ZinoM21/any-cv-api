from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain.dtos import SignedUrl


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
