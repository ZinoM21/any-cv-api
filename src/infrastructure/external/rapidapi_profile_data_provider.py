import json
from typing import Dict

from src.config import Settings
from src.core.exceptions import HTTPException, handle_exceptions
from src.core.interfaces import ILogger, IProfileDataProvider

from .base_api_adapter import BaseApiAdapter


class RapidAPIProfileDataProvider(BaseApiAdapter, IProfileDataProvider):
    def __init__(self, logger: ILogger, settings: Settings):
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": settings.RAPIDAPI_HOST,
            "x-rapidapi-key": settings.RAPIDAPI_KEY,
        }
        super().__init__(
            logger=logger,
            settings=settings,
            base_url=settings.RAPIDAPI_URL,
            headers=headers,
        )

    @handle_exceptions()
    async def get_profile_data_by_username(self, username: str) -> Dict | None:
        """
        Fetch LinkedIn profile data by username.

        Args:
            username: LinkedIn username

        Returns:
            Profile data as dictionary
        """
        payload = {"link": f"https://www.linkedin.com/in/{username}"}
        return await self.post(json_data=payload, handle_busy_response=True)
