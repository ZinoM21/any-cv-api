from abc import ABC, abstractmethod
from typing import Optional

from ..domain.models import User
from ..dtos import PublishingOptionsUpdate, UpdateProfile


class IProfileService(ABC):

    @abstractmethod
    def extract_username(self, link: str) -> str:
        """Extract and validate LinkedIn username from URL or direct input"""
        pass

    @abstractmethod
    async def create_profile_for_user_from_remote_data(
        self, username: str, user: User
    ) -> dict:
        """Create a new profile connected to a user entity"""
        pass

    @abstractmethod
    async def create_guest_profile_from_remote_data(self, username: str) -> dict:
        """Create a new guest profile from remote data"""
        pass

    @abstractmethod
    async def get_profile(self, username: str, user: Optional[User] = None) -> dict:
        """Get a profile"""
        pass

    @abstractmethod
    async def get_published_profiles(self) -> list[dict]:
        """Get all published profiles"""
        pass

    @abstractmethod
    async def get_published_profile(self, slug: str) -> dict:
        """Get a published profile"""
        pass

    @abstractmethod
    async def update_profile(
        self, username: str, data: UpdateProfile, user: Optional[User] = None
    ) -> dict:
        """Update a profile"""
        pass

    @abstractmethod
    async def delete_profile(self, username: str, user: User) -> None:
        """Delete a profile"""
        pass

    @abstractmethod
    async def delete_profiles_from_user(self, user: User) -> None:
        """Delete multiple profiles and all associated files"""
        pass

    @abstractmethod
    async def publish_profile(
        self, username: str, data: PublishingOptionsUpdate, user: User
    ) -> dict:
        """Publish a profile"""
        pass

    @abstractmethod
    async def unpublish_profile(self, username: str, user: User) -> dict:
        """Unpublish a profile"""
        pass

    @abstractmethod
    async def transfer_guest_profile_to_user(self, username: str, user: User) -> dict:
        """Transfer a guest profile to a user profile after sign-in"""
        pass

    @abstractmethod
    async def get_user_profiles(self, user: User) -> list[dict]:
        """Get all profiles associated with a user"""
        pass
