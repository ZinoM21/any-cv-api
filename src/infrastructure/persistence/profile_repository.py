from typing import Optional, Dict

from src.domain.entities.profile import Profile
from src.config.logger import logger


class ProfileRepository:
    async def find_by_username(self, username: str) -> Optional[Profile]:
        try:
            return await Profile.find_one(Profile.username == username)
        except Exception as e:
            logger.error(f"Repository error finding profile: {str(e)}")
            raise

    async def create(self, profile_data: Dict) -> Profile:
        try:
            profile = Profile(**profile_data)
            await profile.create()
            return profile
        except Exception as e:
            logger.error(f"Repository error creating profile: {str(e)}")
            raise
