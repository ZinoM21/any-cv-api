from datetime import datetime, timezone
from uuid import uuid4

from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    ListField,
    StringField,
    UUIDField,
)


class Position(EmbeddedDocument):
    title = StringField(max_length=255, required=True)
    startDate = DateTimeField()
    endDate = DateTimeField()
    duration = StringField(max_length=255)
    description = StringField()
    location = StringField(max_length=255)
    workSetting = StringField(max_length=255)


class Experience(EmbeddedDocument):
    company = StringField(max_length=255, required=True)
    companyProfileUrl = StringField(max_length=255)
    companyLogoUrl = StringField(max_length=255)
    positions = EmbeddedDocumentListField(Position, required=True)


class Education(EmbeddedDocument):
    school = StringField(max_length=255, required=True)
    schoolProfileUrl = StringField(max_length=255)
    schoolPictureUrl = StringField(max_length=255)
    degree = StringField(max_length=255, required=True)
    fieldOfStudy = StringField(max_length=255)
    startDate = DateTimeField()
    endDate = DateTimeField()
    grade = StringField(max_length=255)
    activities = StringField()
    description = StringField()


class VolunteeringExperience(EmbeddedDocument):
    role = StringField(required=True)
    organization = StringField(required=True)
    organizationProfileUrl = StringField(max_length=255)
    organizationLogoUrl = StringField(max_length=255)
    startDate = DateTimeField()
    endDate = DateTimeField()
    cause = StringField(max_length=255)
    description = StringField()


class Project(EmbeddedDocument):
    title = StringField(max_length=255, required=True)
    startDate = DateTimeField()
    endDate = DateTimeField()
    description = StringField()
    url = StringField(max_length=255)
    thumbnail = StringField(max_length=255)
    associatedWith = StringField(max_length=255)


class PublishingOptions(EmbeddedDocument):
    appearance = StringField(max_length=255)
    templateId = StringField(max_length=255)
    slug = StringField(max_length=30)  # sparse index


class Profile(Document):
    id = UUIDField(binary=False, default=uuid4, primary_key=True)
    username = StringField(max_length=255)
    firstName = StringField(max_length=255)
    lastName = StringField(max_length=255)
    profilePictureUrl = StringField(max_length=255)
    jobTitle = StringField(max_length=255)
    headline = StringField(max_length=100)
    about = StringField(max_length=2600)
    email = StringField(max_length=255)
    phone = StringField(max_length=255)
    website = StringField(max_length=255)
    location = StringField(max_length=255)
    languages = ListField(StringField(max_length=255))
    experiences = EmbeddedDocumentListField(Experience)
    education = EmbeddedDocumentListField(Education)
    skills = ListField(StringField(max_length=255))
    volunteering = EmbeddedDocumentListField(VolunteeringExperience)
    projects = EmbeddedDocumentListField(Project)
    publishingOptions = EmbeddedDocumentField(PublishingOptions)
    created_at = DateTimeField(default=datetime.now(timezone.utc))
    updated_at = DateTimeField(default=datetime.now(timezone.utc))

    meta = {
        "collection": "profiles",
        "indexes": [
            {
                "fields": ["publishingOptions.slug"],
                "unique": True,
                "sparse": True,
            }  # sparse allows multiple unpublished profiles
        ],
    }
