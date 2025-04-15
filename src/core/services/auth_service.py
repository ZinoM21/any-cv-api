from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from fastapi import HTTPException, status
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
from src.core.domain.interfaces import IAuthService, ILogger, IUserRepository
from src.core.domain.models import User
from src.infrastructure.exceptions import UnauthorizedHTTPException, handle_exceptions


class AuthService(IAuthService):
    def __init__(
        self, user_repository: IUserRepository, logger: ILogger, settings: Settings
    ):
        self.user_repository = user_repository
        self.logger = logger
        self.pwd_context = CryptContext(schemes=["bcrypt"])
        self.settings = settings

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def encode_with_expiry(self, data: dict, expires_in_minutes: int) -> str:
        data.update(
            {
                "exp": datetime.now(timezone.utc)
                + timedelta(minutes=expires_in_minutes),
                "iat": datetime.now(timezone.utc),
            }
        )

        return jwt.encode(
            data, self.settings.auth_secret, algorithm=self.settings.auth_algorithm
        )

    def decode_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.settings.auth_secret,
            algorithms=[self.settings.auth_algorithm],
        )

    def create_tokens(self, user: User, type: Optional[str] = None) -> dict:
        data_to_encode = {
            "sub": str(user.id),
            "email": user.email,
        }

        if type == "refresh":
            return {
                "access": self.encode_with_expiry(
                    data_to_encode, self.settings.access_token_expire_minutes
                ),
            }

        return {
            "access": self.encode_with_expiry(
                data_to_encode, self.settings.access_token_expire_minutes
            ),
            "refresh": self.encode_with_expiry(
                data_to_encode, self.settings.refresh_token_expire_minutes
            ),
        }

    @handle_exceptions()
    async def authenticate_user(self, request_data: UserLogin) -> TokensResponse:
        user = self.user_repository.find_by_email(request_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with this email",
            )

        if not self.verify_password(request_data.password, str(user.pw_hash)):
            raise UnauthorizedHTTPException(
                detail="Incorrect password",
            )

        tokens = self.create_tokens(user)
        return TokensResponse(**tokens)

    @handle_exceptions()
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        existing_email = self.user_repository.find_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = self.get_password_hash(user_data.password)

        new_user = self.user_repository.create(
            {
                "pw_hash": hashed_password,
                **user_data.model_dump(exclude={"password"}),
            }
        )

        return UserResponse(
            id=UUID(str(new_user.id)),
            email=str(new_user.email),
            firstName=str(new_user.firstName),
            lastName=str(new_user.lastName),
        )

    @handle_exceptions()
    async def refresh_token(self, refresh_token: str) -> AccessResponse:
        try:
            payload = self.decode_token(refresh_token)
        except ExpiredSignatureError:
            raise UnauthorizedHTTPException(detail="Refresh token has expired")
        except InvalidTokenError:
            raise UnauthorizedHTTPException(detail="Invalid refresh token")

        email = payload.get("email")
        if email is None:
            raise UnauthorizedHTTPException(
                detail="Invalid refresh token",
            )

        user = self.user_repository.find_by_email(email)
        if user is None:
            raise UnauthorizedHTTPException(detail="User not found")

        new_access_token = self.create_tokens(user, "refresh")
        return AccessResponse(**new_access_token)
