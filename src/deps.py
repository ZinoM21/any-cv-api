from typing import Annotated
from fastapi import Depends

from src.core.domain.interfaces import ILogger, ILinkedInAPI, IProfileRepository

from src.infrastructure.external import LinkedInAPI
from src.infrastructure.database import Database, ProfileRepository
from src.infrastructure.logging import UvicornLogger

from src.useCases.services import ProfileService, IProfileService


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
def get_linkedin_api(logger: LoggerDep) -> ILinkedInAPI:
    return LinkedInAPI(logger)


# Repositories
def get_profile_repository(logger: LoggerDep) -> IProfileRepository:
    return ProfileRepository(logger)


# Services
def get_profile_service(
    profile_repository: Annotated[IProfileRepository, Depends(get_profile_repository)],
    linkedin_api: Annotated[ILinkedInAPI, Depends(get_linkedin_api)],
    logger: LoggerDep,
) -> IProfileService:
    return ProfileService(profile_repository, linkedin_api, logger)
