from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, StringConstraints

# Type aliases for common string constraints
Str255 = Annotated[str, StringConstraints(max_length=255)]
Str100 = Annotated[str, StringConstraints(max_length=100)]
Str30 = Annotated[str, StringConstraints(max_length=30)]
Str2600 = Annotated[str, StringConstraints(max_length=2600)]


class PositionUpdate(BaseModel):
    title: Str255
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    duration: Optional[Str255] = None
    description: Optional[str] = None
    location: Optional[Str255] = None
    workSetting: Optional[Str255] = None


class ExperienceUpdate(BaseModel):
    company: Str255
    companyProfileUrl: Optional[Str255] = None
    companyLogoUrl: Optional[Str255] = None
    positions: List[PositionUpdate]


class EducationUpdate(BaseModel):
    school: Str255
    schoolProfileUrl: Optional[Str255] = None
    schoolPictureUrl: Optional[Str255] = None
    degree: Str255
    fieldOfStudy: Optional[Str255] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    grade: Optional[Str255] = None
    activities: Optional[str] = None
    description: Optional[str] = None


class VolunteeringExperienceUpdate(BaseModel):
    role: Str255
    organization: Str255
    organizationProfileUrl: Optional[Str255] = None
    organizationLogoUrl: Optional[Str255] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    cause: Optional[Str255] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Str255
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    description: Optional[str] = None
    url: Optional[Str255] = None
    associatedWith: Optional[Str255] = None
    thumbnail: Optional[Str255] = None


class PublishingOptionsUpdate(BaseModel):
    appearance: Optional[Str255] = None
    templateId: Optional[Str255] = None
    slug: Optional[Str30] = None


class UpdateProfile(BaseModel):
    firstName: Optional[Str255] = None
    lastName: Optional[Str255] = None
    profilePictureUrl: Optional[Str255] = None
    jobTitle: Optional[Str255] = None
    headline: Optional[Str100] = None
    about: Optional[Str2600] = None
    email: Optional[Str255] = None
    phone: Optional[Str255] = None
    website: Optional[Str255] = None
    location: Optional[Str255] = None
    languages: Optional[List[Str255]] = None
    experiences: Optional[List[ExperienceUpdate]] = None
    education: Optional[List[EducationUpdate]] = None
    skills: Optional[List[Str255]] = None
    volunteering: Optional[List[VolunteeringExperienceUpdate]] = None
    projects: Optional[List[ProjectUpdate]] = None
    publishingOptions: Optional[PublishingOptionsUpdate] = None


class CreateProfile(BaseModel):
    turnstileToken: Optional[str] = None


class PublishProfileOptions(BaseModel):
    appearance: Str255
    templateId: Str255
    slug: Str30
