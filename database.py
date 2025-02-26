from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db_name: str = "any_cv_db"

    @classmethod
    async def connect(cls):
        # Get MongoDB connection string from environment variable
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        cls.client = AsyncIOMotorClient(mongodb_url)

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()

    @classmethod
    def get_database(cls):
        if not cls.client:
            raise Exception("Database not connected. Call connect() first.")
        return cls.client[cls.db_name]
