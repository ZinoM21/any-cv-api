import re
import json
from typing import Dict, Optional

from src.config import logger
from src.infrastructure.persistence import ProfileRepository
from src.infrastructure.external import LinkedInAPI
from src.utils import transform_profile_data


class ProfileService:
    def __init__(
        self, profile_repository: ProfileRepository, linkedin_api: LinkedInAPI
    ):
        self.profile_repository = profile_repository
        self.linkedin_api = linkedin_api

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
        logger.debug(f"Extracted username: {username}")

        # Check cache / db first
        cached_profile = await self.profile_repository.find_by_username(username)
        if cached_profile:
            logger.debug(f"Profile data found in db for: {username}. Returning...")
            return json.loads(cached_profile.json(exclude={"id": True}))

        # Fetch from LinkedIn if not in cache
        raw_profile_data = await self.linkedin_api.fetch_profile(username)
        logger.debug(f"Profile data fetched from LinkedIn for: {username}")

        # Transform linkedin_api data
        profile_data = transform_profile_data(raw_profile_data)
        logger.debug(f"Profile data transformed for: {username}")

        # Create and save new profile
        profile = await self.profile_repository.create(profile_data)
        logger.debug(f"Profile data saved to db for: {username}")

        return json.loads(profile.json(exclude={"id": True}))
