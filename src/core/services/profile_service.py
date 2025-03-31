import json
import re
from typing import Dict

from fastapi.exceptions import HTTPException, RequestValidationError

from src.core.domain.interfaces import (
    IDataTransformer,
    ILogger,
    IProfileRepository,
    IRemoteDataSource,
)
from src.core.domain.models import UpdateProfile


class ProfileService:
    def __init__(
        self,
        profile_repository: IProfileRepository,
        remote_data_source: IRemoteDataSource,
        logger: ILogger,
        data_transformer: IDataTransformer,
    ):
        self.profile_repository = profile_repository
        self.remote_data_source = remote_data_source
        self.logger = logger
        self.data_transformer = data_transformer

    def __extract_username(self, link: str) -> str:
        """Extract and validate LinkedIn username from URL or direct input"""
        username = link.strip()

        if "/" in username:
            match = re.match(
                r"^(?:https?:\/\/)?(?:[\w]+\.)?linkedin\.com\/in\/([\w\-]+)\/?.*$",
                username,
            )
            if not match:
                raise RequestValidationError("Invalid LinkedIn URL format")
            return match.group(1)

        if not re.match(r"^[\w\-]+$", username):
            raise RequestValidationError("Invalid username format")

        return username

    async def get_profile_info(self, link: str) -> Dict:
        """Get profile information from cache or remote data source"""
        username = self.__extract_username(link)
        self.logger.debug(f"Extracted username: {username}")

        # Check cache / db first
        cached_profile = await self.profile_repository.find_by_username(username)
        if cached_profile:
            self.logger.debug(f"Profile record found in db for: {username}.")
            return json.loads(
                cached_profile.model_dump_json(
                    exclude={"id": True, "updated_at": True, "created_at": True}
                )
            )

        # Fetch from LinkedIn if not in cache
        raw_profile_data = await self.remote_data_source.get_profile_data_by_username(
            username
        )
        self.logger.debug(
            f"Profile data fetched from remote Data Source for: {username}"
        )

        # Transform raw profile data
        profile = await self.data_transformer.transform_profile_data(raw_profile_data)
        if not profile:
            raise HTTPException(
                status_code=500,
                detail="Could not use the fetched data to create a profile",
            )
        self.logger.debug(f"Profile data transformed for: {username}")

        # Check if profile data matches the username
        if profile.username != username:
            raise HTTPException(
                status_code=500,
                detail="Fetched data does not match requested username: {username}",
            )

        # Create and save new profile / cache profile
        profile = await self.profile_repository.create(profile)
        self.logger.debug(f"Profile record created for: {username}")

        return json.loads(
            profile.model_dump_json(
                exclude={"id": True, "updated_at": True, "created_at": True}
            )
        )

    async def get_profile(self, username: str) -> Dict:
        profile = await self.profile_repository.find_by_username(username)

        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Profile not found for username: {username}"
            )

        return json.loads(
            profile.model_dump_json(
                exclude={"id": True, "updated_at": True, "created_at": True}
            )
        )

    async def update_profile(self, username: str, data: UpdateProfile) -> dict:
        """Update a user profile with the provided data"""
        profile = await self.profile_repository.find_by_username(username)

        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Profile not found for username: {username}"
            )

        data_dict = data.model_dump(
            exclude_unset=True,
        )

        updated_profile = await self.profile_repository.update(profile, data_dict)

        return json.loads(
            updated_profile.model_dump_json(
                exclude={"id": True, "updated_at": True, "created_at": True}
            )
        )
