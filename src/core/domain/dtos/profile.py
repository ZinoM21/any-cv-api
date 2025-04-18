from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PositionUpdate(BaseModel):
    title: str
    startDate: datetime
    endDate: Optional[datetime] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    workSetting: Optional[str] = None


class ExperienceUpdate(BaseModel):
    company: str
    companyProfileUrl: Optional[str] = None
    companyLogoUrl: Optional[str] = None
    positions: List[PositionUpdate]


class EducationUpdate(BaseModel):
    school: str
    schoolProfileUrl: Optional[str] = None
    schoolPictureUrl: Optional[str] = None
    degree: str
    fieldOfStudy: Optional[str] = None
    startDate: datetime
    endDate: Optional[datetime] = None
    grade: Optional[str] = None
    activities: Optional[str] = None
    description: Optional[str] = None


class VolunteeringExperienceUpdate(BaseModel):
    role: str
    organization: str
    organizationProfileUrl: Optional[str] = None
    organizationLogoUrl: Optional[str] = None
    startDate: datetime
    endDate: Optional[datetime] = None
    cause: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: str
    startDate: datetime
    endDate: Optional[datetime] = None
    description: Optional[str] = None
    url: Optional[str] = None
    associatedWith: Optional[str] = None
    thumbnail: Optional[str] = None


class PublishingOptionsUpdate(BaseModel):
    appearance: Optional[str] = None
    templateId: Optional[str] = None
    slug: Optional[str] = None


class UpdateProfile(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    profilePictureUrl: Optional[str] = None
    jobTitle: Optional[str] = None
    headline: Optional[str] = None
    about: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[List[str]] = None
    experiences: Optional[List[ExperienceUpdate]] = None
    education: Optional[List[EducationUpdate]] = None
    skills: Optional[List[str]] = None
    volunteering: Optional[List[VolunteeringExperienceUpdate]] = None
    projects: Optional[List[ProjectUpdate]] = None
    publishingOptions: Optional[PublishingOptionsUpdate] = None
