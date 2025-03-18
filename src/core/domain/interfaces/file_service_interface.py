from abc import ABC, abstractmethod
from typing import Dict, List


class IFileService(ABC):
    @abstractmethod
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
            Dict containing the presigned URL and other metadata
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
