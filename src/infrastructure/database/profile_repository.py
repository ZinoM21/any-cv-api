from datetime import datetime, timezone
from typing import Optional

from mongoengine import DoesNotExist

from src.core.domain.interfaces import ILogger, IProfileRepository
from src.core.domain.models import Profile
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class ProfileRepository(IProfileRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    def find_by_username(self, username: str) -> Optional[Profile]:
        try:
            return Profile.objects.get(username=username)
        except DoesNotExist:
            return None

    @handle_exceptions()
    def create(self, profile: Profile) -> Profile:
        return profile.save(cascade=True)

    @handle_exceptions()
    def update(self, profile: Profile, new_data: dict) -> Profile:
        new_data["updated_at"] = datetime.now(timezone.utc)

        for key, value in new_data.items():
            setattr(profile, key, value)

        return profile.save()
