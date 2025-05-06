from abc import ABC, abstractmethod
from typing import Dict


class IRemoteDataSource(ABC):
    @abstractmethod
    async def get_profile_data_by_username(self, username: str) -> Dict | None:
        pass
