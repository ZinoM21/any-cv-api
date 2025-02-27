from beanie import Document, Indexed
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4


class ProfileInfoRequest(BaseModel):
    link: str


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
    Cause: str
    startDate: str
    endDate: Optional[str] = None
    description: str


class Profile(Document):
    id: UUID = Field(default_factory=uuid4)
    username: Indexed(str, unique=True)  # indexed field for faster lookups
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profiles"
        use_revision = True  # enable optimistic concurrency control

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), UUID: lambda v: str(v)}
