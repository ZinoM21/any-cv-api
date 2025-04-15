from datetime import datetime, timezone
from typing import Optional

from mongoengine import DoesNotExist

from src.core.domain.interfaces import ILogger, IProfileCacheRepository
from src.core.domain.models import (
    Education,
    Experience,
    GuestProfile,
    Position,
    Project,
    PublishingOptions,
    VolunteeringExperience,
)
from src.infrastructure.exceptions import handle_exceptions


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
        new_data["updated_at"] = datetime.now(timezone.utc)

        # Handle nested documents properly
        if "education" in new_data:
            education_data = new_data.pop("education")
            if education_data is not None:
                guest_profile.education = [Education(**edu) for edu in education_data]

        if "experiences" in new_data:
            experiences_data = new_data.pop("experiences")
            if experiences_data is not None:
                # Create Experience documents with nested Position documents
                experiences = []
                for exp in experiences_data:
                    positions_data = exp.pop("positions", [])
                    experience = Experience(**exp)
                    experience.positions = [Position(**pos) for pos in positions_data]
                    experiences.append(experience)
                guest_profile.experiences = experiences

        if "volunteering" in new_data:
            volunteering_data = new_data.pop("volunteering")
            if volunteering_data is not None:
                guest_profile.volunteering = [
                    VolunteeringExperience(**vol) for vol in volunteering_data
                ]

        if "projects" in new_data:
            projects_data = new_data.pop("projects")
            if projects_data is not None:
                guest_profile.projects = [Project(**proj) for proj in projects_data]

        if "publishingOptions" in new_data:
            publishing_data = new_data.pop("publishingOptions")
            if publishing_data is not None:
                guest_profile.publishingOptions = PublishingOptions(**publishing_data)

        for key, value in new_data.items():
            setattr(guest_profile, key, value)

        return guest_profile.save()

    @handle_exceptions()
    def delete(self, guest_profile: GuestProfile) -> None:
        guest_profile.save()
        guest_profile.delete()
