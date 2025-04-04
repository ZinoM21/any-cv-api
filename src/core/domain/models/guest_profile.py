from datetime import datetime, timezone
from typing import Annotated, List, Optional
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from .profile import Education, Experience, Project, VolunteeringExperience


class GuestProfile(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore
    username: str
    firstName: str
    lastName: str
    profilePictureUrl: Optional[str] = None
    jobTitle: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    languages: List[str] = []
    experiences: List[Experience] = []
    education: List[Education] = []
    skills: List[str] = []
    volunteering: List[VolunteeringExperience] = []
    projects: List[Project] = []
    created_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(timezone.utc))
    ]
    updated_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(timezone.utc))
    ]

    class Settings:
        name = "guest_profiles"
        use_revision = True
        validate_on_save = True
        indexes = [
            IndexModel(
                "username",
                unique=True,
            ),
            IndexModel(
                "created_at",
                expireAfterSeconds=604800,  # 7 days
            ),
        ]
