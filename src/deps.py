from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.config import Settings, settings
from src.core.domain.interfaces import (
    IAuthService,
    IDataTransformer,
    IFileService,
    ILogger,
    IProfileRepository,
    IRemoteDataSource,
    IUserRepository,
)
from src.core.services import AuthService, ProfileService
from src.core.services.supabase_file_service import SupabaseFileService
from src.infrastructure.database import Database, ProfileRepository, UserRepository
from src.infrastructure.external import LinkedInAPI
from src.infrastructure.logging import UvicornLogger
from src.infrastructure.transformers.data_transformer import DataTransformer


# Config
@lru_cache
def get_settings():
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


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


# Repositories
def get_profile_repository(logger: LoggerDep) -> IProfileRepository:
    return ProfileRepository(logger)


def get_user_repository(logger: LoggerDep) -> IUserRepository:
    return UserRepository(logger)


# Services


# File Service
def get_file_service(logger: LoggerDep, settings: SettingsDep) -> IFileService:
    return SupabaseFileService(logger, settings)


FileServiceDep = Annotated[IFileService, Depends(get_file_service)]


# Data Transformer
def get_data_transformer(
    logger: LoggerDep, settings: SettingsDep, file_service: FileServiceDep
) -> IDataTransformer:
    return DataTransformer(logger, settings, file_service)


def get_profile_service(
    profile_repository: Annotated[IProfileRepository, Depends(get_profile_repository)],
    remote_data_source: Annotated[IRemoteDataSource, Depends(get_linkedin_api)],
    data_transformer: Annotated[IDataTransformer, Depends(get_data_transformer)],
    logger: LoggerDep,
) -> ProfileService:
    return ProfileService(
        profile_repository,
        remote_data_source,
        logger,
        data_transformer,
    )


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


def get_auth_service(
    user_repository: Annotated[IUserRepository, Depends(get_user_repository)],
    logger: LoggerDep,
    settings: SettingsDep,
) -> IAuthService:
    return AuthService(user_repository, logger, settings)


AuthServiceDep = Annotated[IAuthService, Depends(get_auth_service)]
