from abc import ABC, abstractmethod

from src.core.domain.models import Profile


class IDataTransformer(ABC):
    @abstractmethod
    def transform_profile_data(self, data: dict) -> Profile | None:
        pass
