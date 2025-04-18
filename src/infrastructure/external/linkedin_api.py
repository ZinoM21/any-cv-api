import json
import time
from typing import Dict

import requests

# import requests
from fastapi import HTTPException, status

from src.config import Settings
from src.core.domain.interfaces import ILogger, IRemoteDataSource
from src.infrastructure.exceptions import (
    ApiErrorType,
    handle_exceptions,
)


class LinkedInAPI(IRemoteDataSource):
    def __init__(self, logger: ILogger, settings: Settings):
        self.settings = settings
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": self.settings.rapidapi_host,
            "x-rapidapi-key": self.settings.rapidapi_key,
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

        while retries < self.settings.MAX_RETRIES:
            try:

                payload = {"link": f"https://www.linkedin.com/in/{username}"}
                response = requests.post(
                    self.settings.rapidapi_url, json=payload, headers=self.headers
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=ApiErrorType.ResourceNotFound.value,
                    )

                if response.status_code != 200:
                    if "busy" in str(response.text).lower():
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=ApiErrorType.ServiceUnavailable.value,
                        )

                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=ApiErrorType.ServiceUnavailable.value,
                    )

                return response.json()

            except Exception as e:
                last_exception = e
                retries += 1
                self.logger.warn(
                    f"{str(e)} (attempt {retries}/{self.settings.MAX_RETRIES}). Retrying..."
                )

                if retries < self.settings.MAX_RETRIES:
                    time.sleep(self.settings.RETRY_DELAY_SECONDS)
                else:
                    raise e from last_exception
