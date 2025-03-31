from abc import ABC, abstractmethod
from typing import Optional

from src.core.domain.models.file import ImageDownload, SignedUrl


class IFileService(ABC):
    @abstractmethod
    async def generate_signed_url(self, file_path: str) -> SignedUrl:
        """
        Generate a signed URL for file upload

        Args:
            file_path: Path of the file in storage

        Returns:
            SignedUrl containing the signed URL
        """
        pass

    @abstractmethod
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
            SignedUrl containing the signed URL
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
    async def download_remote_image(self, image_url: str) -> Optional[ImageDownload]:
        """
        Download an image from a remote URL

        Args:
            image_url: URL of the remote image

        Returns:
            The image download or None if failed
        """
        pass

    @abstractmethod
    async def upload_image(self, image_download: ImageDownload) -> Optional[str]:
        """
        Upload an image to the file storage

        Args:
            image_download: The image download

        Returns:
            The path of the uploaded file or None if failed
        """
        pass

