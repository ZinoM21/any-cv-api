from datetime import datetime, timezone
from typing import Optional

from mongoengine import DoesNotExist

from src.core.domain.interfaces import ILogger, IProfileRepository
from src.core.domain.models import (
    Education,
    Experience,
    Position,
    Profile,
    Project,
    PublishingOptions,
    VolunteeringExperience,
)
from src.infrastructure.exceptions import handle_exceptions


class ProfileRepository(IProfileRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    @handle_exceptions()
    def find_by_username(self, username: str) -> Optional[Profile]:
        try:
            return Profile.objects.get(username=username)  # type: ignore
        except DoesNotExist:
            return None

    @handle_exceptions()
    def find_by_id(self, profile_id: str) -> Optional[Profile]:
        try:
            return Profile.objects.get(id=profile_id)  # type: ignore
        except DoesNotExist:
            return None

    @handle_exceptions()
    def find_by_ids_and_username(
        self, profile_ids: list[str], username: str
    ) -> list[Profile] | None:
        try:
            profiles = Profile.objects(id__in=profile_ids, username=username)  # type: ignore
            if len(profiles) == 0:
                return None
            return profiles
        except DoesNotExist:
            return None

    @handle_exceptions()
    def create(self, profile: Profile) -> Profile:
        return profile.save(cascade=True)

    @handle_exceptions()
    def update(self, profile: Profile, new_data: dict) -> Profile:
        new_data["updated_at"] = datetime.now(timezone.utc)

        # Handle nested documents properly
        if "education" in new_data:
            education_data = new_data.pop("education")
            if education_data is not None:
                profile.education = [Education(**edu) for edu in education_data]

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
                profile.experiences = experiences

        if "volunteering" in new_data:
            volunteering_data = new_data.pop("volunteering")
            if volunteering_data is not None:
                profile.volunteering = [
                    VolunteeringExperience(**vol) for vol in volunteering_data
                ]

        if "projects" in new_data:
            projects_data = new_data.pop("projects")
            if projects_data is not None:
                profile.projects = [Project(**proj) for proj in projects_data]

        if "publishingOptions" in new_data:
            publishing_data = new_data.pop("publishingOptions")
            if publishing_data:
                profile.publishingOptions = PublishingOptions(**publishing_data)
            else:
                # If publishingOptions is empty, remove it
                if hasattr(profile, "publishingOptions"):
                    profile.publishingOptions = None

        for key, value in new_data.items():
            setattr(profile, key, value)

        return profile.save()

    @handle_exceptions()
    def delete(self, profile: Profile) -> None:
        return profile.delete()

    @handle_exceptions()
    def find_published_profiles(self) -> list[Profile]:
        return Profile.objects.filter(publishingOptions__slug__exists=True)  # type: ignore

    @handle_exceptions()
    def find_published_by_slug(self, slug: str) -> Optional[Profile]:
        try:
            return Profile.objects.get(publishingOptions__slug=slug)  # type: ignore
        except DoesNotExist:
            return None
