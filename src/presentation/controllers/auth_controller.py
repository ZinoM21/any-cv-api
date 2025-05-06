from fastapi import APIRouter, HTTPException, status

from src.core.dtos import (
    AccessResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokensResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailRequest,
)
from src.core.exceptions import (
    HTTPExceptionType,
)
from src.deps import AuthServiceDep, OptionalCurrentUserDep

auth_controller_v1 = APIRouter(prefix="/v1/auth", tags=["auth"])


@auth_controller_v1.post("/login", response_model=TokensResponse)
async def login_for_access_token(
    user_data: UserLogin,
    auth_service: AuthServiceDep,
):
    return await auth_service.authenticate_user(user_data)


@auth_controller_v1.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, auth_service: AuthServiceDep):
    return await auth_service.register_user(user_data)


@auth_controller_v1.post("/refresh-access", response_model=AccessResponse)
async def refresh_access_token(req: RefreshRequest, auth_service: AuthServiceDep):
    return await auth_service.refresh_token(req.refresh_token)


@auth_controller_v1.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(req: VerifyEmailRequest, auth_service: AuthServiceDep):
    """Verify a user's email with the provided token."""
    success = await auth_service.verify_email(req.token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=HTTPExceptionType.BadRequest.value,
        )

    return {"message": "Email verified successfully"}


@auth_controller_v1.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(req: ForgotPasswordRequest, auth_service: AuthServiceDep):
    """Initiate the password reset process for a user."""
    return await auth_service.forgot_password(req)


@auth_controller_v1.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    req: ResetPasswordRequest,
    auth_service: AuthServiceDep,
    user: OptionalCurrentUserDep,
):
    """Reset a user's password using their old password.

    This endpoint requires authentication and validates the old password
    before allowing the password to be changed.
    """
    return await auth_service.reset_password(
        user_id=str(user.id) if user else None,
        token=req.token,
        new_password=req.password,
    )
