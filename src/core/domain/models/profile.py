from datetime import datetime, timezone
from typing import Annotated, List, Optional
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class Position(BaseModel):
    title: str
    startDate: str
    endDate: Optional[str] = None
    duration: Optional[str] = None
    description: str
    location: Optional[str] = None
    workSetting: Optional[str] = None


class Experience(BaseModel):
    company: str
    companyProfileUrl: Optional[str] = None
    companyLogoUrl: Optional[str] = None
    positions: List[Position]


class Education(BaseModel):
    school: str
    schoolProfileUrl: Optional[str] = None
    schoolPictureUrl: Optional[str] = None
    degree: str
    fieldOfStudy: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None
    grade: Optional[str] = None
    activities: Optional[str] = None
    description: Optional[str] = None


class VolunteeringExperience(BaseModel):
    role: str
    organization: str
    organizationProfileUrl: Optional[str] = None
    cause: str
    startDate: str
    endDate: Optional[str] = None
    description: str


class Profile(Document):
    id: UUID = Field(default_factory=uuid4)
    username: Annotated[str, Indexed(unique=True)]
    firstName: str
    lastName: str
    profilePictureUrl: Optional[str] = None
    jobTitle: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
    experiences: List[Experience] = []
    education: List[Education] = []
    skills: List[str] = []
    volunteering: List[VolunteeringExperience] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "profiles"
        use_revision = True  # enable optimistic concurrency control
        validate_on_save = True


class UpdateProfile(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    profilePictureUrl: Optional[str] = None
    jobTitle: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
    experiences: Optional[List[Experience]] = None
    education: Optional[List[Education]] = None
    skills: Optional[List[str]] = None
    volunteering: Optional[List[VolunteeringExperience]] = None
