from abc import ABC, abstractmethod
from typing import Optional

from ..domain.models import Profile


class IDataTransformerService(ABC):
    """Interface for data transformers."""

    @abstractmethod
    async def transform_profile_data(
        self, data: dict, is_authenticated: bool = True, user_id: Optional[str] = None
    ) -> Profile | None:
        pass
