from typing import Dict, Optional

from src.core.domain.interfaces import ILogger, IProfileRepository
from src.core.domain.models import Profile


class ProfileRepository(IProfileRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    async def find_by_username(self, username: str) -> Optional[Profile]:
        try:
            return await Profile.find_one(Profile.username == username)
        except Exception as e:
            self.logger.error(f"Repository error finding profile: {str(e)}")
            raise

    async def create(self, profile_data: Dict) -> Profile:
        try:
            profile = Profile(**profile_data)
            await profile.create()
            return profile
        except Exception as e:
            self.logger.error(f"Repository error creating profile: {str(e)}")
            raise
