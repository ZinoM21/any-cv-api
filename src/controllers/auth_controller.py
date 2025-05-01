from fastapi import APIRouter, HTTPException, status

from src.core.domain.dtos import (
    AccessResponse,
    RefreshRequest,
    TokensResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailRequest,
)
from src.deps import AuthServiceDep
from src.infrastructure.exceptions import (
    ApiErrorType,
    UnauthorizedHTTPException,
)

auth_controller_v1 = APIRouter(prefix="/v1/auth", tags=["auth"])


@auth_controller_v1.post("/login", response_model=TokensResponse)
async def login_for_access_token(
    user_data: UserLogin,
    auth_service: AuthServiceDep,
):
    user = await auth_service.authenticate_user(user_data)
    if not user:
        raise UnauthorizedHTTPException(
            detail=ApiErrorType.InvalidCredentials.value,
        )

    return user


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
            detail=ApiErrorType.BadRequest.value,
        )

    return {"message": "Email verified successfully"}
