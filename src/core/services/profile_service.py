import json
import re
from typing import Dict

from src.core.domain.interfaces import (
    IDataTransformer,
    ILogger,
    IProfileRepository,
    IRemoteDataSource,
)


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
                raise ValueError("Invalid LinkedIn URL format")
            return match.group(1)

        if not re.match(r"^[\w\-]+$", username):
            raise ValueError("Invalid username format")

        return username

    async def get_profile_info(self, link: str) -> Dict:
        """Get profile information from cache or remote data source"""
        username = self.__extract_username(link)
        self.logger.debug(f"Extracted username: {username}")

        # Check cache / db first
        cached_profile = await self.profile_repository.find_by_username(username)
        if cached_profile:
            self.logger.debug(f"Profile record found in db for: {username}.")
            return json.loads(cached_profile.json(exclude={"id": True}))

        # Fetch from LinkedIn if not in cache
        raw_profile_data = await self.remote_data_source.get_profile_data_by_username(
            username
        )
        self.logger.debug(
            f"Profile data fetched from remote Data Source for: {username}"
        )

        # Transform raw profile data
        profile = self.data_transformer.transform_profile_data(raw_profile_data)
        self.logger.debug(f"Profile data transformed for: {username}")

        # Create and save new profile / cache profile
        profile = await self.profile_repository.create(profile)
        self.logger.debug(f"Profile record created for: {username}")

        return json.loads(profile.json(exclude={"id": True}))
