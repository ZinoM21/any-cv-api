from functools import lru_cache
from typing import Annotated, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import Settings, settings
from src.core.domain.interfaces import (
    IProfileCacheRepository,
    IProfileRepository,
    IUserRepository,
)
from src.core.domain.models import User
from src.core.exceptions import HTTPExceptionType, UnauthorizedHTTPException
from src.core.interfaces import (
    IAuthService,
    IDataTransformerService,
    IEmailService,
    IFileService,
    ILogger,
    IProfileService,
    IRemoteDataSource,
    IUserService,
)
from src.core.services import (
    AuthService,
    DataTransformerService,
    ProfileService,
    ResendEmailService,
    SupabaseFileService,
    UserService,
)
from src.core.utils import decode_jwt
from src.infrastructure.external import LinkedInAPI
from src.infrastructure.logging import UvicornLogger
from src.infrastructure.persistence import (
    Database,
    ProfileCacheRepository,
    ProfileRepository,
    UserRepository,
)


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


RemoteDataSourceDep = Annotated[IRemoteDataSource, Depends(get_linkedin_api)]


# Email
def get_email_service(logger: LoggerDep, settings: SettingsDep) -> IEmailService:
    return ResendEmailService(logger, settings)


EmailServiceDep = Annotated[IEmailService, Depends(get_email_service)]


# Repositories
def get_profile_repository(logger: LoggerDep) -> IProfileRepository:
    return ProfileRepository(logger)


ProfileRepositoryDep = Annotated[IProfileRepository, Depends(get_profile_repository)]


def get_profile_cache_repository(logger: LoggerDep) -> IProfileCacheRepository:
    return ProfileCacheRepository(logger)


ProfileCacheRepositoryDep = Annotated[
    IProfileCacheRepository, Depends(get_profile_cache_repository)
]


def get_user_repository(logger: LoggerDep) -> IUserRepository:
    return UserRepository(logger)


UserRepositoryDep = Annotated[IUserRepository, Depends(get_user_repository)]


# Services


# File Service
def get_file_service(
    logger: LoggerDep,
    settings: SettingsDep,
    profile_repository: ProfileRepositoryDep,
) -> IFileService:
    return SupabaseFileService(logger, settings, profile_repository)


FileServiceDep = Annotated[IFileService, Depends(get_file_service)]


# Data Transformer Service
def get_data_transformer_service(
    logger: LoggerDep, settings: SettingsDep, file_service: FileServiceDep
) -> IDataTransformerService:
    return DataTransformerService(logger, settings, file_service)


DataTransformerServiceDep = Annotated[
    IDataTransformerService, Depends(get_data_transformer_service)
]


def get_profile_service(
    profile_repository: ProfileRepositoryDep,
    profile_cache_repository: ProfileCacheRepositoryDep,
    user_repository: UserRepositoryDep,
    remote_data_source: RemoteDataSourceDep,
    file_service: FileServiceDep,
    data_transformer: DataTransformerServiceDep,
    logger: LoggerDep,
    settings: SettingsDep,
) -> IProfileService:
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


ProfileServiceDep = Annotated[IProfileService, Depends(get_profile_service)]


# User Service
def get_user_service(
    user_repository: UserRepositoryDep,
    profile_service: ProfileServiceDep,
    logger: LoggerDep,
) -> IUserService:
    return UserService(user_repository, profile_service, logger)


UserServiceDep = Annotated[IUserService, Depends(get_user_service)]


# Auth
def get_auth_service(
    user_repository: UserRepositoryDep,
    crypto_context: CryptoContextDep,
    email_service: EmailServiceDep,
    logger: LoggerDep,
    settings: SettingsDep,
) -> IAuthService:
    return AuthService(user_repository, crypto_context, email_service, logger, settings)


AuthServiceDep = Annotated[IAuthService, Depends(get_auth_service)]


# User
security = HTTPBearer(auto_error=False)


async def get_current_user(
    bearer_header: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    user_repo: UserRepositoryDep,
) -> User:
    if not bearer_header:
        raise UnauthorizedHTTPException(detail=HTTPExceptionType.InvalidToken.value)

    payload = decode_jwt(
        bearer_header.credentials,
        secret=settings.AUTH_SECRET,
        algorithm=settings.AUTH_ALGORITHM,
    )

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedHTTPException(detail=HTTPExceptionType.InvalidToken.value)

    user = user_repo.find_by_id(user_id)
    if not user:
        raise UnauthorizedHTTPException(detail=HTTPExceptionType.InvalidToken.value)

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# Optional User

optional_auth_scheme = HTTPBearer(auto_error=False)


async def get_optional_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_auth_scheme)
    ],
    user_repository: UserRepositoryDep,
) -> Optional[User]:
    """
    Dependency that retrieves the authenticated user if available,
    but returns None instead of raising an exception if not authenticated.
    """
    if not credentials:
        return None

    payload = decode_jwt(
        credentials.credentials,
        secret=settings.AUTH_SECRET,
        algorithm=settings.AUTH_ALGORITHM,
    )

    user_id = payload.get("sub")
    if not user_id:
        return None

    return user_repository.find_by_id(user_id)


OptionalCurrentUserDep = Annotated[Optional[User], Depends(get_optional_current_user)]
