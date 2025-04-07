from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
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
