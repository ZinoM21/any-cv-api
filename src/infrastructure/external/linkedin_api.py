import time
from typing import Dict

import requests
from fastapi import status

from src.config import Settings
from src.core.exceptions import HTTPException, HTTPExceptionType, handle_exceptions
from src.core.interfaces import ILogger, IRemoteDataSource


class LinkedInAPI(IRemoteDataSource):
    def __init__(self, logger: ILogger, settings: Settings):
        self.settings = settings
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": self.settings.RAPIDAPI_HOST,
            "x-rapidapi-key": self.settings.RAPIDAPI_KEY,
        }
        self.logger = logger

    @handle_exceptions()
    async def get_profile_data_by_username(self, username: str) -> Dict | None:
        # # TODO: Replace with actual API call
        # try:
        #     with open(f"try/{username}.json", "r") as file:
        #         return json.load(file)
        # except FileNotFoundError:
        #     raise HTTPException(
        #         status_code=404, detail=f"No Profile under username {username}"
        #     )

        retries = 0
        last_exception = None

        while retries < self.settings.EXTERNAL_MAX_RETRIES:
            try:

                payload = {"link": f"https://www.linkedin.com/in/{username}"}
                response = requests.post(
                    self.settings.RAPIDAPI_URL, json=payload, headers=self.headers
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=HTTPExceptionType.ResourceNotFound.value,
                    )

                if response.status_code != 200:
                    if "busy" in str(response.text).lower():
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=HTTPExceptionType.ServiceUnavailable.value,
                        )

                    raise Exception(
                        f"Error fetching profile data from RapidAPI: {response.text}",
                    )

                return response.json()

            except Exception as e:
                last_exception = e
                retries += 1
                self.logger.warn(
                    f"{str(e)} (attempt {retries}/{self.settings.EXTERNAL_MAX_RETRIES}). Retrying..."
                )

                if retries < self.settings.EXTERNAL_MAX_RETRIES:
                    time.sleep(self.settings.EXTERNAL_RETRY_DELAY_SECONDS)
                else:
                    raise e from last_exception
