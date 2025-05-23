import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import status
from passlib.context import CryptContext

from src.config import Settings
from src.core.domain.interfaces import (
    IUserRepository,
)
from src.core.domain.models import User
from src.core.dtos import (
    AccessResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    PasswordResetResponse,
    TokensResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.core.exceptions import (
    HTTPException,
    HTTPExceptionType,
    UnauthorizedHTTPException,
    handle_exceptions,
)
from src.core.interfaces import (
    IAuthService,
    IEmailService,
    ILogger,
    ITurnstileVerifier,
)
from src.core.utils import decode_jwt, encode_with_expiry


class AuthService(IAuthService):
    def __init__(
        self,
        user_repository: IUserRepository,
        crypto_context: CryptContext,
        email_service: IEmailService,
        turnstile_verifier: ITurnstileVerifier,
        logger: ILogger,
        settings: Settings,
    ):
        self.user_repository = user_repository
        self.crypto_context = crypto_context
        self.email_service = email_service
        self.turnstile_verifier = turnstile_verifier
        self.logger = logger
        self.settings = settings

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.crypto_context.verify(plain_password, hashed_password)

    def _get_password_hash(self, password: str) -> str:
        return self.crypto_context.hash(password)

    def _create_tokens(self, user: User, type: Optional[str] = None) -> dict[str, str]:
        if user.firstName or user.lastName:
            data_to_encode = {
                "sub": str(user.id),
                "email": user.email,
                "name": (f"{user.firstName or ''} {user.lastName or ''}").strip(),
            }
        else:
            data_to_encode = {
                "sub": str(user.id),
                "email": user.email,
            }

        if type == "refresh":
            return {
                "access": encode_with_expiry(
                    data_to_encode,
                    self.settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES,
                    self.settings.AUTH_SECRET,
                    self.settings.AUTH_ALGORITHM,
                ),
            }

        return {
            "access": encode_with_expiry(
                data_to_encode,
                self.settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES,
                self.settings.AUTH_SECRET,
                self.settings.AUTH_ALGORITHM,
            ),
            "refresh": encode_with_expiry(
                data_to_encode,
                self.settings.REFRESH_TOKEN_EXPIRES_IN_MINUTES,
                self.settings.AUTH_SECRET,
                self.settings.AUTH_ALGORITHM,
            ),
        }

    @handle_exceptions()
    async def _generate_and_store_email_verify_token(self, user_id: str) -> str:
        """Generate a random token for email verification and store it in the database."""
        # 1. Generate a random token
        alphabet = string.ascii_letters + string.digits
        token = "".join(secrets.choice(alphabet) for _ in range(64))
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.EMAIL_VERIFICATION_EXPIRES_IN_HOURS
        )

        # 2. Store the token in the database
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=HTTPExceptionType.ResourceNotFound.value,
            )

        user = self.user_repository.update(
            user,
            {"verification_token": token, "verification_token_expires": expires_at},
        )

        return token

    @handle_exceptions()
    async def authenticate_user(self, request_data: UserLogin) -> TokensResponse:
        user = self.user_repository.find_by_email(request_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=HTTPExceptionType.InvalidCredentials.value,
            )

        if not self._verify_password(request_data.password, str(user.pw_hash)):
            raise UnauthorizedHTTPException(
                detail=HTTPExceptionType.InvalidCredentials.value,
            )

        tokens = self._create_tokens(user)
        return TokensResponse(**tokens)

    @handle_exceptions()
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        existing_email = self.user_repository.find_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=HTTPExceptionType.ResourceAlreadyExists.value,
            )

        hashed_password = self._get_password_hash(user_data.password)

        new_user = self.user_repository.create(
            {
                "pw_hash": hashed_password,
                **user_data.model_dump(exclude={"password"}),
            }
        )

        # Generate and set verification token
        token = await self._generate_and_store_email_verify_token(str(new_user.id))

        # Send verification email
        name = f"{new_user.firstName} {new_user.lastName}".strip()
        await self.email_service.send_verification_email(
            str(new_user.email), token, name
        )

        return UserResponse(
            id=UUID(str(new_user.id)),
            email=str(new_user.email),
            firstName=str(new_user.firstName),
            lastName=str(new_user.lastName),
            email_verified=bool(new_user.email_verified),
        )

    @handle_exceptions()
    async def refresh_token(self, refresh_token: str) -> AccessResponse:
        payload = decode_jwt(
            refresh_token, self.settings.AUTH_SECRET, self.settings.AUTH_ALGORITHM
        )

        email = payload.get("email")
        if email is None:
            raise UnauthorizedHTTPException(
                detail=HTTPExceptionType.InvalidToken.value,
            )

        user = self.user_repository.find_by_email(email)
        if user is None:
            raise UnauthorizedHTTPException(detail=HTTPExceptionType.InvalidToken.value)

        new_access_token = self._create_tokens(user, "refresh")
        return AccessResponse(**new_access_token)

    @handle_exceptions()
    async def verify_email(self, token: str) -> bool:
        """Verify a user's email with the provided token."""
        user = self.user_repository.find_by_verification_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=HTTPExceptionType.BadRequest.value,
            )

        updated_user = self.user_repository.update(
            user,
            {
                "email_verified": True,
                "verification_token": None,
                "verification_token_expires": None,
            },
        )
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=HTTPExceptionType.InternalServerError.value,
            )

        return True

    @handle_exceptions()
    async def _generate_and_store_password_reset_token(self, user: User) -> str:
        """Generate a random token for password reset and store it in the database.

        Args:
            user: The user to generate a password reset token for

        Returns:
            str: The generated token

        Raises:
            HTTPException: If the user cannot be updated
        """
        # 1. Generate a random token
        alphabet = string.ascii_letters + string.digits
        token = "".join(secrets.choice(alphabet) for _ in range(64))
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.EMAIL_VERIFICATION_EXPIRES_IN_HOURS
        )

        # 2. Store the token in the database
        updated_user = self.user_repository.update(
            user,
            {"password_reset_token": token, "password_reset_token_expires": expires_at},
        )
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=HTTPExceptionType.InternalServerError.value,
            )

        return token

    @handle_exceptions()
    async def forgot_password(
        self, request: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        """Initiate the password reset process for a user.

        Note: For security reasons, this method always returns the same response
        regardless of whether the email exists or not.

        Args:
            request: The forgot password request containing the email

        Returns:
            ForgotPasswordResponse: A response object with a standard message
        """
        user = self.user_repository.find_by_email(request.email)

        if user:
            token = await self._generate_and_store_password_reset_token(user)

            name = f"{user.firstName} {user.lastName}".strip()
            await self.email_service.send_password_reset_email(
                str(user.email), token, name
            )

            self.logger.info(f"Password reset email sent to {user.email}")
        else:
            # Log the attempt but don't reveal
            self.logger.info(
                f"Password reset requested for non-existent email: {request.email}"
            )

        return ForgotPasswordResponse()

    @handle_exceptions()
    async def reset_password(
        self,
        user_id: str | None = None,
        token: str | None = None,
        new_password: str | None = None,
    ) -> PasswordResetResponse:
        """Reset a user's password after verifying the old password.

        Args:
            user_id: The ID of the user
            new_password: The new password

        Returns:
            PasswordResetResponse: A response object with a standard message

        Raises:
            HTTPException: If the old password is invalid or user not found
        """
        if not new_password:
            self.logger.error("No new password provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=HTTPExceptionType.BadRequest.value,
            )

        # This endpoint can only be used by an authed user or from a password reset email
        if user_id:
            user = self.user_repository.find_by_id(user_id)
        elif token:
            user = self.user_repository.find_by_password_reset_token(token)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=HTTPExceptionType.BadRequest.value,
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=HTTPExceptionType.ResourceNotFound.value,
            )

        # Exception if new is same as old
        if self._verify_password(new_password, str(user.pw_hash)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=HTTPExceptionType.BadRequest.value,
            )

        new_hashed_password = self._get_password_hash(new_password)
        updated_user = self.user_repository.update(
            user,
            {
                "pw_hash": new_hashed_password,
                "password_reset_token": None,
                "password_reset_token_expires": None,
            },
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=HTTPExceptionType.InternalServerError.value,
            )

        self.logger.info(f"Password reset successfully for user: {user.email}")
        return PasswordResetResponse(email=str(user.email))
