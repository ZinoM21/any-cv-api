import json
from typing import Dict
import requests

from src.config.logger import logger
from src.config.environment import env


class LinkedInAPI:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": env.rapidapi_host,
            "x-rapidapi-key": env.rapidapi_key,
        }

    async def fetch_profile(self, username: str) -> Dict:
        try:
            # # TODO: Replace with actual API call
            with open("try/rapidAPI-response.json", "r") as file:
                return json.load(file)

            #     response = requests.post(rapidapi_url, json=payload, headers=headers)

            # if response.status_code == 404:
            #     logger.error(
            #         f"RapidAPI request failed with status code: {response.status_code}"
            #     )
            #     return JSONResponse(content={"error": "User not found"}, status_code=404)

            # if response.status_code != 200:
            #     logger.error(
            #         f"RapidAPI request failed with status code: {response.status_code}"
            #     )
            #     raise HTTPException(
            #         status_code=response.status_code,
            #         detail="Failed to fetch data from RapidAPI",
            #     )

            # payload = {"link": f"https://www.linkedin.com/in/{username}"}
            # response = requests.post(
            #     env.rapidapi_url, json=payload, headers=self.headers
            # )

            # if response.status_code == 404:
            #     raise ValueError("Profile not found")

            # response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"LinkedIn API error: {str(e)}")
            raise
