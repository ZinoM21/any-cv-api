from abc import ABC, abstractmethod


class IDataTransformer(ABC):
    @abstractmethod
    def transform_profile_data(self, data: dict) -> dict:
        pass
