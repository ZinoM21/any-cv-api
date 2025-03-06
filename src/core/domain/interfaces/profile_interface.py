from abc import ABC, abstractmethod
from typing import Dict, Optional

from src.core.domain.models import Profile


class IProfileRepository(ABC):
    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[Profile]:
        pass

    @abstractmethod
    async def create(self, profile_data: Dict) -> Profile:
        pass
