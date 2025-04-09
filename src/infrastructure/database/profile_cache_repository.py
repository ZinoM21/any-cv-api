from datetime import datetime, timezone
from typing import Optional

from mongoengine import DoesNotExist

from src.core.domain.interfaces import ILogger, IProfileCacheRepository
from src.core.domain.models import GuestProfile
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class ProfileCacheRepository(IProfileCacheRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    def find_by_username(self, username: str) -> Optional[GuestProfile]:
        try:
            return GuestProfile.objects.get(username=username)
        except DoesNotExist:
            return None

    @handle_exceptions()
    def create(self, guest_profile: GuestProfile) -> GuestProfile:
        return guest_profile.save()

    @handle_exceptions()
    def update(self, guest_profile: GuestProfile, new_data: dict) -> GuestProfile:
        # Set the updated_at field to current timestamp
        new_data["updated_at"] = datetime.now(timezone.utc)

        # Update the document and return the updated version
        return guest_profile.update(**new_data)

    @handle_exceptions()
    def delete(self, guest_profile: GuestProfile) -> None:
        guest_profile.save()
        guest_profile.delete()
