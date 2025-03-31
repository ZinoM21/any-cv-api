from abc import ABC, abstractmethod

from src.core.domain.models import Profile


class IDataTransformer(ABC):
    """Interface for data transformers."""

    def __init__(self, logger, file_service=None):
        self.logger = logger
        self.file_service = file_service

    @abstractmethod
    async def transform_profile_data(self, data: dict) -> Profile | None:
        pass
