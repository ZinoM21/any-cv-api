from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.config import settings
from src.core.domain.interfaces import ILogger
from src.core.domain.models import __beanie_models__


class Database:
    client: AsyncIOMotorClient = None

    @classmethod
    async def connect(cls, logger: ILogger):
        """Initialize database connection and Beanie"""
        try:
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )

            # Initialize Beanie with the MongoDB client and document models
            await init_beanie(
                database=cls.client.any_cv_db, document_models=__beanie_models__
            )

            logger.info("Successfully connected to MongoDB with Beanie")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def disconnect(cls, logger: ILogger):
        """Disconnect from database"""
        if cls.client:
            cls.client.close()
            cls.client = None
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def health_check(cls, logger: ILogger) -> bool:
        """Check database health"""
        try:
            if cls.client:
                await cls.client.admin.command("ping")
                return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
        return False
