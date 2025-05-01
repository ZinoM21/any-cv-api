from functools import lru_cache
from typing import Annotated, Optional

from fastapi import Depends, Request
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import Settings, settings
from src.core.domain.interfaces import (
    IAuthService,
    IDataTransformer,
    IEmailService,
    IFileService,
    ILogger,
    IProfileCacheRepository,
    IProfileRepository,
    IRemoteDataSource,
    IUserRepository,
)
from src.core.domain.models import User
from src.core.services import AuthService, ProfileService
from src.core.services.resend_email_service import ResendEmailService
from src.core.services.supabase_file_service import SupabaseFileService
from src.infrastructure.database import (
    Database,
    ProfileCacheRepository,
    ProfileRepository,
    UserRepository,
)
from src.infrastructure.exceptions import (
    ApiErrorType,
    UnauthorizedHTTPException,
)
from src.infrastructure.external import LinkedInAPI
from src.infrastructure.logging import UvicornLogger
from src.infrastructure.transformers.data_transformer import DataTransformer


# Config
@lru_cache
def get_settings():
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_crypto_context():
    return CryptContext(schemes=["bcrypt"])


CryptoContextDep = Annotated[CryptContext, Depends(get_crypto_context)]


# Limits
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Logging
logger = UvicornLogger()


def get_logger() -> ILogger:
    return logger


LoggerDep = Annotated[ILogger, Depends(get_logger)]


# Database
def get_db():
    return Database


DatabaseDep = Annotated[Database, Depends(get_db)]


# External
def get_linkedin_api(logger: LoggerDep, settings: SettingsDep) -> IRemoteDataSource:
    return LinkedInAPI(logger, settings)


# Email
def get_email_service(logger: LoggerDep, settings: SettingsDep) -> IEmailService:
    return ResendEmailService(logger, settings)


EmailServiceDep = Annotated[IEmailService, Depends(get_email_service)]


# Repositories
def get_profile_repository(logger: LoggerDep) -> IProfileRepository:
    return ProfileRepository(logger)


def get_profile_cache_repository(logger: LoggerDep) -> IProfileCacheRepository:
    return ProfileCacheRepository(logger)


def get_user_repository(logger: LoggerDep) -> IUserRepository:
    return UserRepository(logger)


# Services


# File Service
def get_file_service(
    logger: LoggerDep,
    settings: SettingsDep,
    profile_repository: Annotated[IProfileRepository, Depends(get_profile_repository)],
) -> IFileService:
    return SupabaseFileService(logger, settings, profile_repository)


FileServiceDep = Annotated[IFileService, Depends(get_file_service)]


# Data Transformer
def get_data_transformer(
    logger: LoggerDep, settings: SettingsDep, file_service: FileServiceDep
) -> IDataTransformer:
    return DataTransformer(logger, settings, file_service)


def get_profile_service(
    profile_repository: Annotated[IProfileRepository, Depends(get_profile_repository)],
    profile_cache_repository: Annotated[
        IProfileCacheRepository, Depends(get_profile_cache_repository)
    ],
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
    remote_data_source: Annotated[IRemoteDataSource, Depends(get_linkedin_api)],
    file_service: Annotated[IFileService, Depends(get_file_service)],
    data_transformer: Annotated[IDataTransformer, Depends(get_data_transformer)],
    logger: LoggerDep,
    settings: SettingsDep,
) -> ProfileService:
    return ProfileService(
        profile_repository,
        profile_cache_repository,
        user_repository,
        remote_data_source,
        file_service,
        data_transformer,
        logger,
        settings,
    )


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


# Auth
def get_auth_service(
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
    crypto_context: CryptoContextDep,
    email_service: EmailServiceDep,
    logger: LoggerDep,
    settings: SettingsDep,
) -> IAuthService:
    return AuthService(user_repository, crypto_context, email_service, logger, settings)


AuthServiceDep = Annotated[IAuthService, Depends(get_auth_service)]


# User
async def get_current_user(
    request: Request,
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> User:
    """
    Dependency that retrieves the authenticated user based on the user_id
    set in request.state by the auth middleware. Raises an exception if
    the user is not authenticated.
    """
    if not hasattr(request.state, "user") or not request.state.user:
        raise UnauthorizedHTTPException()

    user_id = request.state.user.get("user_id")
    if not user_id or not isinstance(user_id, str):
        raise UnauthorizedHTTPException()

    user = user_repository.find_by_id(user_id)

    if not user:
        raise UnauthorizedHTTPException(detail=ApiErrorType.InvalidCredentials.value)

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_optional_current_user(
    request: Request,
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> Optional[User]:
    """
    Dependency that retrieves the authenticated user if available,
    but returns None instead of raising an exception if not authenticated.
    """
    if not hasattr(request.state, "user") or not request.state.user:
        return None

    user_id = request.state.user.get("user_id")
    if not user_id:
        return None

    return user_repository.find_by_id(user_id)


OptionalCurrentUserDep = Annotated[Optional[User], Depends(get_optional_current_user)]
