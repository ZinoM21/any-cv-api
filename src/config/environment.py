from dotenv import load_dotenv
import os
from typing import Optional


class Environment:
    def __init__(self):
        load_dotenv()

        # MongoDB
        self.mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

        # RapidAPI
        self.rapidapi_url: Optional[str] = os.getenv("RAPIDAPI_URL")
        self.rapidapi_host: Optional[str] = os.getenv("RAPIDAPI_HOST")
        self.rapidapi_key: Optional[str] = os.getenv("RAPIDAPI_KEY")

        # Frontend
        self.frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

        # LinkedIn
        self.li_username: Optional[str] = os.getenv("LI_USERNAME")
        self.li_password: Optional[str] = os.getenv("LI_PASSWORD")

    def validate(self) -> None:
        """Validate all environment variables"""
        for attr, value in self.__dict__.items():
            if value is None:
                env_var = attr.upper()
                if os.getenv(env_var) is None:
                    raise ValueError(f"Missing environment variable: {env_var}")


env = Environment()
