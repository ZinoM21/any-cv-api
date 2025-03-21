from fastapi import APIRouter, HTTPException, status

from src.core.domain.models.user import UserCreate, UserLogin, UserResponse
from src.deps import AuthServiceDep, LoggerDep

auth_controller_v1 = APIRouter(prefix="/v1/auth", tags=["auth"])


@auth_controller_v1.post("/login")
async def login_for_access_token(
    user_data: UserLogin,
    auth_service: AuthServiceDep,
    logger: LoggerDep,
):
    user = await auth_service.authenticate_user(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@auth_controller_v1.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, auth_service: AuthServiceDep):
    return await auth_service.register_user(user_data)
