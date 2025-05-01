import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
import requests
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from src.config import Settings
from src.core.domain.dtos import (
    AccessResponse,
    TokensResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.core.domain.interfaces import (
    IAuthService,
    IEmailService,
    ILogger,
    IUserRepository,
)
from src.core.domain.models import User
from src.infrastructure.exceptions import (
    ApiErrorType,
    UnauthorizedHTTPException,
    handle_exceptions,
)


class AuthService(IAuthService):
    def __init__(
        self,
        user_repository: IUserRepository,
        crypto_context: CryptContext,
        email_service: IEmailService,
        logger: ILogger,
        settings: Settings,
    ):
        self.user_repository = user_repository
        self.crypto_context = crypto_context
        self.email_service = email_service
        self.logger = logger
        self.settings = settings

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.crypto_context.verify(plain_password, hashed_password)

    def _get_password_hash(self, password: str) -> str:
        return self.crypto_context.hash(password)

    def _encode_with_expiry(self, data: dict, expires_in_minutes: int) -> str:
        data.update(
            {
                "exp": datetime.now(timezone.utc)
                + timedelta(minutes=expires_in_minutes),
                "iat": datetime.now(timezone.utc),
            }
        )

        return jwt.encode(
            data, self.settings.AUTH_SECRET, algorithm=self.settings.AUTH_ALGORITHM
        )

    def _decode_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.settings.AUTH_SECRET,
            algorithms=[self.settings.AUTH_ALGORITHM],
        )

    def _create_tokens(self, user: User, type: Optional[str] = None) -> dict:
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
                "access": self._encode_with_expiry(
                    data_to_encode, self.settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES
                ),
            }

        return {
            "access": self._encode_with_expiry(
                data_to_encode, self.settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES
            ),
            "refresh": self._encode_with_expiry(
                data_to_encode, self.settings.REFRESH_TOKEN_EXPIRES_IN_MINUTES
            ),
        }

    @handle_exceptions(origin="AuthService._generate_and_store_email_verify_token")
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
                detail=ApiErrorType.ResourceNotFound.value,
            )

        user = self.user_repository.update(
            user,
            {"verification_token": token, "verification_token_expires": expires_at},
        )

        return token

    @handle_exceptions(origin="AuthService.authenticate_user")
    async def authenticate_user(self, request_data: UserLogin) -> TokensResponse:
        user = self.user_repository.find_by_email(request_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiErrorType.InvalidCredentials.value,
            )

        if not self._verify_password(request_data.password, str(user.pw_hash)):
            raise UnauthorizedHTTPException(
                detail=ApiErrorType.InvalidCredentials.value,
            )

        tokens = self._create_tokens(user)
        return TokensResponse(**tokens)

    @handle_exceptions(origin="AuthService.register_user")
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        existing_email = self.user_repository.find_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ApiErrorType.ResourceAlreadyExists.value,
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

    @handle_exceptions(origin="AuthService.refresh_token")
    async def refresh_token(self, refresh_token: str) -> AccessResponse:
        try:
            payload = self._decode_token(refresh_token)
        except ExpiredSignatureError:
            raise UnauthorizedHTTPException(detail=ApiErrorType.TokenExpired.value)
        except InvalidTokenError:
            raise UnauthorizedHTTPException(detail=ApiErrorType.InvalidToken.value)

        email = payload.get("email")
        if email is None:
            raise UnauthorizedHTTPException(
                detail=ApiErrorType.InvalidToken.value,
            )

        user = self.user_repository.find_by_email(email)
        if user is None:
            raise UnauthorizedHTTPException(detail=ApiErrorType.InvalidToken.value)

        new_access_token = self._create_tokens(user, "refresh")
        return AccessResponse(**new_access_token)

    @handle_exceptions(origin="AuthService.verify_turnstile")
    async def verify_turnstile(self, token: str, remote_ip: str | None = None) -> bool:
        """
        Verify a Turnstile token againt an external service

        Args:
            token: The token to verify
            remote_ip: Optional IP address of the user

        Returns:
            bool: True if verification was successful

        Raises:
            HTTPException: If verification fails
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ApiErrorType.BadRequest.value,
            )

        data = {
            "secret": self.settings.TURNSTILE_SECRET_KEY,
            "response": token,
        }

        if remote_ip:
            data["remoteip"] = remote_ip

        try:
            response = requests.post(self.settings.TURNSTILE_CHALLENGE_URL, json=data)

            verify_response = response.json()
            if not verify_response.get("success"):
                error_codes = verify_response.get("error-codes") or []
                self.logger.error(f"Turnstile verification failed: {error_codes}")
                if (
                    "invalid-input-response" in error_codes
                    or "missing-input-response" in error_codes
                ):
                    raise RequestValidationError(
                        errors=[
                            {
                                "loc": ["body", "turnstileToken"],
                                "msg": "Turnstile token is invalid",
                            }
                        ]
                    )
                elif "bad-request" in error_codes:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=ApiErrorType.BadRequest.value,
                    )
                elif "timeout-or-duplicate" in error_codes:
                    raise RequestValidationError(
                        errors=[
                            {
                                "loc": ["body", "turnstileToken"],
                                "msg": "Turnstile token already used",
                            }
                        ]
                    )
                elif "internal-error" in error_codes:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=ApiErrorType.ServiceUnavailable.value,
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=ApiErrorType.InternalServerError.value,
                    )

            self.logger.debug("Request validated against Turnstile")
            return True

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to verify Turnstile token: {str(e)}"
            )

    @handle_exceptions(origin="AuthService.verify_email")
    async def verify_email(self, token: str) -> bool:
        """Verify a user's email with the provided token."""
        user = self.user_repository.find_by_verification_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ApiErrorType.BadRequest.value,
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
                detail=ApiErrorType.InternalServerError.value,
            )

        return True
