from abc import ABC, abstractmethod

from ..dtos import (
    AccessResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    PasswordResetResponse,
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

    @abstractmethod
    async def forgot_password(
        self, request: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        """Initiates the password reset process

        Args:
            request: The forgot password request

        Returns:
            ForgotPasswordResponse: Response confirming the request was processed

        Raises:
            HTTPException: If there's an error processing the request
        """
        pass

    @abstractmethod
    async def reset_password(
        self,
        user_id: str | None = None,
        token: str | None = None,
        new_password: str | None = None,
    ) -> PasswordResetResponse:
        """Resets a user's password after verifying the old password

        Args:
            user_id: The ID of the user
            new_password: The new password
            token: The token to reset the password
        Returns:
            PasswordResetResponse: A response object with a standard message

        Raises:
            HTTPException: If the old password is invalid or user not found
        """
        pass
