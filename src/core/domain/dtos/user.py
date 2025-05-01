from typing import Annotated, Optional
from uuid import UUID

import resend
from pydantic import BaseModel, EmailStr, StringConstraints

# Type alias for common string constraint
Str255 = Annotated[str, StringConstraints(max_length=255)]


class UserCreate(BaseModel):
    email: EmailStr  # EmailField in MongoEngine with max_length=255
    password: Str255  # Based on pw_hash field which has max_length=255
    firstName: Optional[Str255] = None
    lastName: Optional[Str255] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: Str255


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    firstName: Optional[Str255] = None
    lastName: Optional[Str255] = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    firstName: Str255
    lastName: Str255
    email_verified: bool = False


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    password: Str255
    token: Optional[str] = None


class ForgotPasswordResponse(BaseModel):
    message: str = (
        "If your email exists in our system, a password reset link has been sent."
    )


class PasswordResetResponse(BaseModel):
    email: EmailStr


class Email(resend.Email):
    pass


class Attachment(resend.Attachment):
    pass


class Tag(resend.Tag):
    pass
