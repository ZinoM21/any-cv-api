from abc import ABC, abstractmethod
from typing import Optional

from pydantic import EmailStr

from src.core.domain.models.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: EmailStr) -> Optional[User]:
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        pass
