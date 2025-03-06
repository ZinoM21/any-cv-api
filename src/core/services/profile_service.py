import json
import re
from abc import ABC, abstractmethod
from typing import Dict

from src.core.domain.interfaces import ILinkedInAPI, ILogger, IProfileRepository
from src.utils import transform_profile_data


class IProfileService(ABC):
    @abstractmethod
    def extract_username(self, link: str) -> str:
        pass

    @abstractmethod
    async def get_profile_info(self, link: str) -> Dict:
        pass


class ProfileService(IProfileService):
    def __init__(
        self,
        profile_repository: IProfileRepository,
        linkedin_api: ILinkedInAPI,
        logger: ILogger,
    ):
        self.profile_repository = profile_repository
        self.linkedin_api = linkedin_api
        self.logger = logger

    def extract_username(self, link: str) -> str:
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
        """Get profile information from cache or LinkedIn"""
        username = self.extract_username(link)
        self.logger.debug(f"Extracted username: {username}")

        # Check cache / db first
        cached_profile = await self.profile_repository.find_by_username(username)
        if cached_profile:
            self.logger.debug(f"Profile data found in db for: {username}. Returning...")
            return json.loads(cached_profile.json(exclude={"id": True}))

        # Fetch from LinkedIn if not in cache
        raw_profile_data = await self.linkedin_api.fetch_profile(username)
        self.logger.debug(f"Profile data fetched from LinkedIn for: {username}")

        # Transform linkedin_api data
        profile_data = transform_profile_data(raw_profile_data)
        self.logger.debug(f"Profile data transformed for: {username}")

        # Create and save new profile
        profile = await self.profile_repository.create(profile_data)
        self.logger.debug(f"Profile data saved to db for: {username}")

        return json.loads(profile.json(exclude={"id": True}))
