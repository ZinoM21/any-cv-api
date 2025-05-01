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

    @abstractmethod
    async def verify_turnstile(self, token: str, remote_ip: str | None = None) -> bool:
        """Verify a Turnstile token

        Args:
            token: The token to verify
            remote_ip: Optional IP address of the user

        Returns:
            bool: True if verification was successful

        Raises:
            HTTPException: If verification fails
        """
        pass

    @abstractmethod
    async def verify_email(self, token: str) -> bool:
        """Verify a user's email with the provided token

        Args:
            token: The verification token

        Returns:
            bool: True if verification was successful

        Raises:
            HTTPException: If verification fails
        """
        pass
