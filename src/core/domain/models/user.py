from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID, uuid4

from beanie import Document, Indexed  # type: ignore
from pydantic import BaseModel, EmailStr, Field


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

