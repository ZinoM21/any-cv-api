from mongoengine import connect, disconnect

from src.config import settings
from src.core.interfaces import ILogger


class Database:
    @classmethod
    def connect(cls, logger: ILogger):
        """Initialize database connection and Beanie"""
        try:
            connect("anycv", host=settings.MONGODB_URL)
            logger.info("Successfully connected to MongoDB with MongoEngine")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    def disconnect(cls, logger: ILogger):
        """Disconnect from database"""
        disconnect()
        logger.info("Disconnected from MongoDB")
