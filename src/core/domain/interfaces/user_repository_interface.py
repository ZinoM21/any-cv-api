from abc import ABC, abstractmethod
from typing import Optional

from pydantic import EmailStr

from src.core.domain.models import Profile, User


class IUserRepository(ABC):
    @abstractmethod
    def find_by_email(self, email: EmailStr) -> Optional[User]:
        pass

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    def create(self, user: dict) -> User:
        pass

    @abstractmethod
    def append_profile_to_user(self, profile: Profile, user: User) -> User:
        pass
