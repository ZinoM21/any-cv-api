from datetime import datetime, timezone
from typing import Annotated, List, Optional
from uuid import UUID, uuid4

from beanie import Document, Indexed, Link  # type: ignore
from pydantic import BaseModel, EmailStr, Field

from .profile import Profile


class User(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore
    username: Annotated[str, Indexed(unique=True)]
    email: Annotated[EmailStr, Indexed(unique=True)]
    pw_hash: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    created_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(timezone.utc))
    ]
    updated_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(timezone.utc))
    ]
    profiles: Optional[List[Link[Profile]]] = None

    class Settings:
        name = "users"
        use_revision = True
        validate_on_save = True


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    firstName: str
    lastName: str


class TokensResponse(BaseModel):
    access: str
    refresh: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessResponse(BaseModel):
    access: str
