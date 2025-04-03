from typing import Optional

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
    async def create(self, user: User) -> User:
        return await user.create()
