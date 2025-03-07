from typing import Optional

from src.core.decorators import handle_exceptions
from src.core.domain.interfaces import ILogger, IProfileRepository
from src.core.domain.models import Profile


class ProfileRepository(IProfileRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    async def find_by_username(self, username: str) -> Optional[Profile]:
        return await Profile.find_one(Profile.username == username)

    @handle_exceptions()
    async def create(self, profile: Profile):
        return await profile.create()
