from typing import List, Optional

from beanie.operators import Or
from pydantic import EmailStr

from src.core.domain.interfaces import ILogger, IUserRepository
from src.core.domain.models.user import User
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class UserRepository(IUserRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    async def find_by_email(self, email: EmailStr) -> Optional[User]:
        return await User.find_one(User.email == email)

    @handle_exceptions()
    async def find_by_username_or_email(
        self, username: str, email: str
    ) -> Optional[List[User]]:
        return await User.find(
            Or(User.username == username, User.email == email)
        ).to_list()

    @handle_exceptions()
    async def find_by_username(self, username: str) -> Optional[User]:
        return await User.find_one(User.username == username)

    @handle_exceptions()
    async def create(self, user: User) -> User:
        return await user.create()
