from datetime import datetime, timezone
from typing import Optional

from src.core.domain.interfaces import ILogger, IProfileRepository
from src.core.domain.models import Profile
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class ProfileRepository(IProfileRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    async def find_by_username(self, username: str) -> Optional[Profile]:
        return await Profile.find_one(Profile.username == username)

    @handle_exceptions()
    async def create(self, profile: Profile) -> Profile:
        return await profile.create()

    @handle_exceptions()
    async def update(self, profile: Profile, new_data: dict) -> Profile:
        # Set the updated_at field to current timestamp
        new_data["updated_at"] = datetime.now(timezone.utc)

        # Update the document and return the updated version
        updated_profile = await profile.update({"$set": new_data})

        return updated_profile
