from datetime import datetime, timezone
from typing import Optional

from mongoengine import DoesNotExist
from pydantic import EmailStr

from src.core.domain.interfaces import IUserRepository
from src.core.domain.models import Profile, User
from src.core.exceptions import handle_exceptions


class UserRepository(IUserRepository):
    def __init__(self):
        pass

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
        user.update(push__profiles=profile)
        return user.reload()

    @handle_exceptions()
    def delete(self, user: User) -> bool:
        """Delete a user and all associated profiles.

        Args:
            user: The user to delete

        Returns:
            bool: True if deletion was successful, raises an exception otherwise
        """
        user.delete()
        return True
