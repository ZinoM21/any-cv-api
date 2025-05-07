from mongoengine import connect, disconnect
from pymongo import MongoClient

from src.core.interfaces import ILogger


class Database:
    @classmethod
    def connect(cls, mongodb_url: str, logger: ILogger):
        """Initialize database connection and Beanie"""
        try:
            connect(
                "anycv",
                host=mongodb_url,
                uuidRepresentation="standard",
                mongo_client_class=MongoClient,
                alias="default",
            )
            logger.info("Successfully connected to MongoDB with MongoEngine")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    def disconnect(cls, logger: ILogger):
        """Disconnect from database"""
        disconnect()
        logger.info("Disconnected from MongoDB")
