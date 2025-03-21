from abc import ABC, abstractmethod

from src.core.domain.models.user import UserCreate, UserLogin, UserResponse


class IAuthService(ABC):
    @abstractmethod
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        pass

    @abstractmethod
    async def authenticate_user(self, user_data: UserLogin) -> UserResponse:
        """Authenticate a user and return the user if credentials are valid"""
        pass
