from mongoengine import connect, disconnect

from src.core.domain.interfaces import ILogger
from src.deps import settings


class Database:
    @classmethod
    async def connect(cls, logger: ILogger):
        """Initialize database connection and Beanie"""
        try:
            connect("anycv", host=settings.mongodb_url)
            logger.info("Successfully connected to MongoDB with MongoEngine")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def disconnect(cls, logger: ILogger):
        """Disconnect from database"""
        disconnect()
        logger.info("Disconnected from MongoDB")
