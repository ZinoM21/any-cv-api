from fastapi import APIRouter, Request

from src.core.domain.dtos import UpdateProfile
from src.deps import (
    CurrentUserDep,
    OptionalCurrentUserDep,
    ProfileServiceDep,
    limiter,
)
from src.infrastructure.exceptions import handle_exceptions

profile_controller_v1 = APIRouter(prefix="/v1/profile", tags=["profile"])


@profile_controller_v1.get("/healthz")
async def healthz():
    return {"status": "ok"}


@profile_controller_v1.get("/published")
@handle_exceptions()
async def get_published_profiles(
    profile_service: ProfileServiceDep,
):
    """
    Get all published profiles.
    This endpoint is used for pre-rendering published profiles for SSG.
    """
    return await profile_service.get_published_profiles()


@profile_controller_v1.get("/published/{username}")
@handle_exceptions()
async def get_published_profile(
    username: str,
    profile_service: ProfileServiceDep,
):
    """
    Get a published profile.
    This endpoint is used for pre-rendering published profiles for SSG.
    """
    return await profile_service.get_published_profile(username)


@profile_controller_v1.get("/{username}")
@handle_exceptions()
async def get_profile(
    username: str,
    profile_service: ProfileServiceDep,
    user: OptionalCurrentUserDep,
):
    return await profile_service.get_profile(username, user)


@profile_controller_v1.post("/{username}")
@limiter.limit("3/minute; 10/day")
@handle_exceptions()
async def create_profile(
    request: Request,
    username: str,
    profile_service: ProfileServiceDep,
    user: OptionalCurrentUserDep,
):
    return await profile_service.create_profile(username, user)


@profile_controller_v1.patch("/{username}")
@handle_exceptions()
async def update_profile(
    username: str,
    profile_data: UpdateProfile,
    profile_service: ProfileServiceDep,
    user: OptionalCurrentUserDep,
):
    return await profile_service.update_profile(username, profile_data, user)


@profile_controller_v1.get("/{username}/transfer")
@handle_exceptions()
async def transfer_guest_profile(
    username: str,
    profile_service: ProfileServiceDep,
    user: CurrentUserDep,
):
    """
    Transfer a guest profile to an authenticated user's profile.
    This endpoint should be called after a user signs in or signs up.
    Requires authentication.
    """
    return await profile_service.transfer_guest_profile_to_user(username, user)


@profile_controller_v1.get("/user/list")
@handle_exceptions()
async def get_user_profiles(
    profile_service: ProfileServiceDep,
    user: CurrentUserDep,
):
    """
    Get all profiles associated with the authenticated user.
    Requires authentication.
    """
    return await profile_service.get_user_profiles(user)
