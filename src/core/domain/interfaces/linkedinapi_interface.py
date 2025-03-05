from typing import Dict
from abc import ABC, abstractmethod


class ILinkedInAPI(ABC):
    @abstractmethod
    async def fetch_profile(self, username: str) -> Dict:
        pass
