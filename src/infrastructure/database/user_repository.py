from typing import Optional

from mongoengine import DoesNotExist
from pydantic import EmailStr

from src.core.domain.interfaces import ILogger, IUserRepository
from src.core.domain.models import Profile, User
from src.infrastructure.exceptions import handle_exceptions


class UserRepository(IUserRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    def find_by_email(self, email: EmailStr) -> Optional[User]:
        try:
            return User.objects.get(email=email)  # type: ignore
        except DoesNotExist:
            return None

    @handle_exceptions()
    def find_by_id(self, user_id: str) -> Optional[User]:
        try:
            return User.objects.get(id=user_id)  # type: ignore
        except DoesNotExist:
            return None

    @handle_exceptions()
    def create(self, user: dict) -> User:
        return User(**user).save()

    @handle_exceptions()
    def append_profile_to_user(self, profile: Profile, user: User) -> User:
        try:
            self.logger.debug(f"Appending profile {profile.username} to user: {user.id}")
            User.objects(id=user.id).update_one(push__profiles=profile)  # type: ignore
            return user.save()
        except Exception as e:
            self.logger.error(f"Error appending profile to user: {e}")
            raise e
