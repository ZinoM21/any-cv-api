from datetime import datetime, timezone
from typing import Optional

from src.core.domain.interfaces import ILogger, IProfileCacheRepository
from src.core.domain.models import GuestProfile
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class ProfileCacheRepository(IProfileCacheRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    async def find_by_username(self, username: str) -> Optional[GuestProfile]:
        return await GuestProfile.find_one(GuestProfile.username == username)

    @handle_exceptions()
    async def create(self, profile: GuestProfile) -> GuestProfile:
        return await profile.create()

    @handle_exceptions()
    async def update(self, profile: GuestProfile, new_data: dict) -> GuestProfile:
        # Set the updated_at field to current timestamp
        new_data["updated_at"] = datetime.now(timezone.utc)

        # Update the document and return the updated version
        return await profile.update({"$set": new_data})
