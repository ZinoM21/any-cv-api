from typing import Optional
from uuid import UUID

from beanie import WriteRules
from pydantic import EmailStr

from src.core.domain.interfaces import ILogger, IUserRepository
from src.core.domain.models import Profile, User
from src.infrastructure.exceptions import handle_exceptions


class UserRepository(IUserRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    async def find_by_email(self, email: EmailStr) -> Optional[User]:
        return await User.find_one(User.email == email)

    @handle_exceptions()
    async def find_by_id(self, user_id: str) -> Optional[User]:
        return await User.get(UUID(user_id))

    @handle_exceptions()
    async def create(self, user: User) -> User:
        return await user.create()

    @handle_exceptions()
    async def append_profile_to_user(self, profile: Profile, user: User) -> User:
        user.profiles = [profile]
        return await user.save(link_rule=WriteRules.WRITE)
