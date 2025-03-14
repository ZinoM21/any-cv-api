from typing import Dict

import requests
from fastapi.exceptions import HTTPException

from src.config import settings
from src.core.decorators import handle_exceptions
from src.core.domain.interfaces import ILogger, IRemoteDataSource


class LinkedInAPI(IRemoteDataSource):
    def __init__(self, logger: ILogger):
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": settings.rapidapi_host,
            "x-rapidapi-key": settings.rapidapi_key,
        }
        self.logger = logger

    @handle_exceptions()
    async def get_profile_data_by_username(self, username: str) -> Dict:
        # # TODO: Replace with actual API call
        # try:
        #     with open(f"try/{username}.json", "r") as file:
        #         return json.load(file)
        # except FileNotFoundError:
        #     raise HTTPException(
        #         status_code=404, detail=f"No Profile under username {username}"
        #     )

        payload = {"link": f"https://www.linkedin.com/in/{username}"}
        response = requests.post(
            settings.rapidapi_url, json=payload, headers=self.headers
        )

        if response.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"No Profile found for username {username}"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Error fetching profile data from external API",
            )

        return response.json()
