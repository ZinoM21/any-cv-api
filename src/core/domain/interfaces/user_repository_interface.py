from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import EmailStr

from src.core.domain.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: EmailStr) -> Optional[User]:
        pass

    @abstractmethod
    async def find_by_username_or_email(
        self, username: str, email: str
    ) -> Optional[List[User]]:
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        pass
