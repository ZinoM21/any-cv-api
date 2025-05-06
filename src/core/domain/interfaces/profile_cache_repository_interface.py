from abc import ABC, abstractmethod
from typing import Optional

from ..models import GuestProfile


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
