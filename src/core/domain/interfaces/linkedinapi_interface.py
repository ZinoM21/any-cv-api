from abc import ABC, abstractmethod
from typing import Dict


class ILinkedInAPI(ABC):
    @abstractmethod
    async def fetch_profile(self, username: str) -> Dict:
        pass
