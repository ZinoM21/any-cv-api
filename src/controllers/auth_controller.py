from fastapi import APIRouter

from src.core.domain.models.user import (
    AccessResponse,
    RefreshRequest,
    TokensResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.core.exceptions import UnauthorizedHTTPException
from src.deps import AuthServiceDep

auth_controller_v1 = APIRouter(prefix="/v1/auth", tags=["auth"])


@auth_controller_v1.post("/login", response_model=TokensResponse)
async def login_for_access_token(
    user_data: UserLogin,
    auth_service: AuthServiceDep,
):
    user = await auth_service.authenticate_user(user_data)
    if not user:
        raise UnauthorizedHTTPException(
            detail="Incorrect username or password",
        )

    return user


@auth_controller_v1.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, auth_service: AuthServiceDep):
    return await auth_service.register_user(user_data)


@auth_controller_v1.post("/refresh-access", response_model=AccessResponse)
async def refresh_access_token(req: RefreshRequest, auth_service: AuthServiceDep):
    return await auth_service.refresh_token(req.refresh_token)
