from datetime import datetime, timezone
from uuid import uuid4

from mongoengine import (
    PULL,
    BooleanField,
    DateTimeField,
    Document,
    EmailField,
    ListField,
    ReferenceField,
    StringField,
    UUIDField,
)

from .profile import Profile


class User(Document):
    id = UUIDField(binary=False, default=uuid4, primary_key=True)
    email = EmailField(required=True, unique=True, max_length=255)
    pw_hash = StringField(required=True, max_length=255)
    firstName = StringField(max_length=255)
    lastName = StringField(max_length=255)
    created_at = DateTimeField(default=datetime.now(timezone.utc))
    updated_at = DateTimeField(default=datetime.now(timezone.utc))
    profiles = ListField(ReferenceField(Profile, reverse_delete_rule=PULL))
    email_verified = BooleanField(default=False)
    verification_token = StringField()
    verification_token_expires = DateTimeField()
    password_reset_token = StringField()
    password_reset_token_expires = DateTimeField()

    meta = {"collection": "users", "indexes": ["email"]}
