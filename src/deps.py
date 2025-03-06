from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.config import Settings, settings
from src.core.domain.interfaces import (
    IDataTransformer,
    ILogger,
    IProfileRepository,
    IRemoteDataSource,
)
from src.core.services import ProfileService
from src.infrastructure.database import Database, ProfileRepository
from src.infrastructure.external import LinkedInAPI
from src.infrastructure.logging import UvicornLogger
from src.infrastructure.transformers import DataTransformer


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
def get_db() -> Database:
    return Database


DatabaseDep = Annotated[Database, Depends(get_db)]


# External
def get_linkedin_api(logger: LoggerDep) -> IRemoteDataSource:
    return LinkedInAPI(logger)


# Repositories
def get_profile_repository(logger: LoggerDep) -> IProfileRepository:
    return ProfileRepository(logger)


# Data Transformer
def get_data_transformer(logger: LoggerDep) -> IDataTransformer:
    return DataTransformer(logger)


# Services
def get_profile_service(
    profile_repository: Annotated[IProfileRepository, Depends(get_profile_repository)],
    remote_data_source: Annotated[IRemoteDataSource, Depends(get_linkedin_api)],
    logger: LoggerDep,
    data_transformer: Annotated[IDataTransformer, Depends(get_data_transformer)],
) -> ProfileService:
    return ProfileService(
        profile_repository, remote_data_source, logger, data_transformer
    )


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
