from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from src.domain.entities.profile import Profile
from src.config import env
from src.config import logger


class Database:
    client: AsyncIOMotorClient = None

    @classmethod
    async def connect(cls):
        """Initialize database connection and Beanie"""
        try:
            cls.client = AsyncIOMotorClient(
                env.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )

            # Initialize Beanie with the MongoDB client and document models
            await init_beanie(database=cls.client.any_cv_db, document_models=[Profile])

            logger.info("Successfully connected to MongoDB with Beanie")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def disconnect(cls):
        """Disconnect from database"""
        if cls.client:
            cls.client.close()
            cls.client = None
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def health_check(cls) -> bool:
        """Check database health"""
        try:
            if cls.client:
                await cls.client.admin.command("ping")
                return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
        return False
