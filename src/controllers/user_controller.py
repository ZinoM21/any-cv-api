from fastapi import APIRouter, status

from src.core.domain.dtos import UserResponse, UserUpdate
from src.deps import CurrentUserDep, UserServiceDep

user_controller_v1 = APIRouter(prefix="/v1/user", tags=["user"])


@user_controller_v1.get("/", response_model=UserResponse)
async def get_user(
    user_service: UserServiceDep,
    user: CurrentUserDep,
):
    """Get the current user's information.

    This endpoint requires authentication and returns the user's
    account information.
    """
    return await user_service.get_user(str(user.id))


@user_controller_v1.patch("/", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    user_service: UserServiceDep,
    user: CurrentUserDep,
):
    """Update a user's account information.

    This endpoint requires authentication and allows the user to update their
    account information such as name and email.
    """
    return await user_service.update_user(str(user.id), user_data)


@user_controller_v1.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_service: UserServiceDep,
    user: CurrentUserDep,
):
    """Delete the current user's account and all associated profiles.

    This endpoint requires authentication and will permanently delete the user's
    account and all associated profiles.
    """
    return await user_service.delete_user(str(user.id))
