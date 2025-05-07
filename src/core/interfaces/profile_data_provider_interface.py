from abc import ABC, abstractmethod
from typing import Dict


class IProfileDataProvider(ABC):
    """Interface for profile data providers."""

    @abstractmethod
    async def get_profile_data_by_username(self, username: str) -> Dict | None:
        """
        Fetch profile data by username.

        Args:
            username: Username to fetch profile for

        Returns:
            Profile data as dictionary
        """
        pass
