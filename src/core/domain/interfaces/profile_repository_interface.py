from abc import ABC, abstractmethod
from typing import Optional

from src.core.domain.models import GuestProfile, Profile


class IProfileRepository(ABC):
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[Profile]:
        pass

    @abstractmethod
    def find_by_id(self, profile_id: str) -> Optional[Profile]:
        pass

    @abstractmethod
    def find_by_ids_and_username(
        self, profile_ids: list[str], username: str
    ) -> Optional[list[Profile]]:
        pass

    @abstractmethod
    def create(self, profile: Profile) -> Profile:
        pass

    @abstractmethod
    def update(self, profile: Profile, new_data: dict) -> Profile:
        pass

    @abstractmethod
    def find_published_profiles(self) -> list[Profile]:
        pass

    @abstractmethod
    def find_published_by_slug(self, slug: str) -> Optional[Profile]:
        pass


class IProfileCacheRepository(ABC):
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[GuestProfile]:
        pass

    @abstractmethod
    def create(self, guest_profile: GuestProfile) -> GuestProfile:
        pass

    @abstractmethod
    def update(self, guest_profile: GuestProfile, new_data: dict) -> GuestProfile:
        pass

    @abstractmethod
    def delete(self, guest_profile: GuestProfile) -> None:
        pass
