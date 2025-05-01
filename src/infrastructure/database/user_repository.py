from datetime import datetime, timezone
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
    def find_by_verification_token(self, token: str) -> Optional[User]:
        try:
            return User.objects(  # type: ignore
                verification_token=token,
                verification_token_expires__gt=datetime.now(timezone.utc),
            ).first()
        except DoesNotExist:
            return None

    @handle_exceptions()
    def find_by_password_reset_token(self, token: str) -> Optional[User]:
        try:
            return User.objects(  # type: ignore
                password_reset_token=token,
                password_reset_token_expires__gt=datetime.now(timezone.utc),
            ).first()
        except DoesNotExist:
            return None

    @handle_exceptions()
    def create(self, user: dict) -> User:
        return User(**user).save()

    @handle_exceptions()
    def update(self, user: User, data: dict) -> User:
        for key, value in data.items():
            setattr(user, key, value)
        return user.save()

    @handle_exceptions()
    def append_profile_to_user(self, profile: Profile, user: User) -> User:
        try:
            self.logger.debug(
                f"Appending profile {profile.username} to user: {user.id}"
            )
            User.objects(id=user.id).update_one(push__profiles=profile)  # type: ignore
            return user.save()
        except Exception as e:
            self.logger.error(f"Error appending profile to user: {e}")
            raise e

    @handle_exceptions()
    def delete(self, user: User) -> bool:
        """Delete a user and all associated profiles.

        Args:
            user: The user to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            user.delete()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting user and profiles: {e}")
            return False
