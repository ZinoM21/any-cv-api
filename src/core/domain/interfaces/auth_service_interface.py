from abc import ABC, abstractmethod

from src.core.domain.dtos import (
    AccessResponse,
    TokensResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)


class IAuthService(ABC):
    @abstractmethod
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        pass

    @abstractmethod
    async def authenticate_user(self, request_data: UserLogin) -> TokensResponse:
        """Authenticate a user and return the user if credentials are valid"""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AccessResponse:
        """Refresh access token"""
        pass
