from datetime import datetime, timezone
from uuid import uuid4

from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocumentListField,
    ListField,
    StringField,
    UUIDField,
)

from src.config import settings

from .profile import Education, Experience, Project, VolunteeringExperience


class GuestProfile(Document):
    id = UUIDField(binary=False, default=uuid4, primary_key=True)
    username = StringField(max_length=255, unique=True)
    firstName = StringField(max_length=255)
    lastName = StringField(max_length=255)
    profilePictureUrl = StringField(max_length=255)
    jobTitle = StringField(max_length=255)
    headline = StringField()
    about = StringField()
    email = StringField(max_length=255)
    phone = StringField(max_length=255)
    location = StringField(max_length=255)
    languages = ListField(StringField(max_length=255))
    experiences = EmbeddedDocumentListField(Experience)
    education = EmbeddedDocumentListField(Education)
    skills = ListField(StringField(max_length=255))
    volunteering = EmbeddedDocumentListField(VolunteeringExperience)
    projects = EmbeddedDocumentListField(Project)
    created_at = DateTimeField(default=datetime.now(timezone.utc))
    updated_at = DateTimeField(default=datetime.now(timezone.utc))

    meta = {
        "collection": "guest_profiles",
        "indexes": [
            {
                "fields": ["created_at"],
                "expireAfterSeconds": settings.cache_guest_profile_sec,
            }
        ],
    }
