import json

from src.config import settings
from src.core.domain.interfaces import ILogger, IRemoteDataSource
from src.core.domain.models import Profile


class LinkedInAPI(IRemoteDataSource):
    def __init__(self, logger: ILogger):
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": settings.rapidapi_host,
            "x-rapidapi-key": settings.rapidapi_key,
        }
        self.logger = logger

    async def get_profile_data_by_username(self, username: str) -> Profile:
        try:
            # # TODO: Replace with actual API call
            with open("try/rapidAPI-response.json", "r") as file:
                return json.load(file)

            # if file coulnt be found, raise HTTPException 404
            if not file:
                raise HTTPException(
                    status_code=404, detail="No Profile under this username"
                )

            #     response = requests.post(rapidapi_url, json=payload, headers=headers)

            # if response.status_code == 404:
            #     self.logger.error(
            #         f"RapidAPI request failed with status code: {response.status_code}"
            #     )
            #     return JSONResponse(content={"error": "User not found"}, status_code=404)

            # if response.status_code != 200:
            #     self.logger.error(
            #         f"RapidAPI request failed with status code: {response.status_code}"
            #     )
            #     raise HTTPException(
            #         status_code=response.status_code,
            #         detail="Failed to fetch data from RapidAPI",
            #     )

            # payload = {"link": f"https://www.linkedin.com/in/{username}"}
            # response = requests.post(
            #     settings.rapidapi_url, json=payload, headers=self.headers
            # )

            # if response.status_code == 404:
            #     raise ValueError("Profile not found")

            # response.raise_for_status()
            # return response.json()

        except Exception as e:
            self.logger.error(f"LinkedIn API error: {str(e)}")
            raise
