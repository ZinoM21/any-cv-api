from fastapi import APIRouter, HTTPException, Request, status

from src.core.domain.dtos import CreateProfile, PublishingOptionsUpdate, UpdateProfile
from src.deps import (
    AuthServiceDep,
    CurrentUserDep,
    OptionalCurrentUserDep,
    ProfileServiceDep,
    limiter,
)
from src.infrastructure.exceptions import (
    ApiErrorType,
    handle_exceptions,
)

profile_controller_v1 = APIRouter(prefix="/v1/profile", tags=["profile"])


# PUBLIC ROUTES
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


@profile_controller_v1.get("/published/{slug}")
@handle_exceptions()
async def get_published_profile(
    slug: str,
    profile_service: ProfileServiceDep,
):
    """
    Get a published profile.
    This endpoint is used for pre-rendering published profiles for SSG.
    """
    return await profile_service.get_published_profile(slug)


# OPTIONAL AUTH ROUTES
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
    turnstile_data: CreateProfile,
    profile_service: ProfileServiceDep,
    auth_service: AuthServiceDep,
    user: OptionalCurrentUserDep,
):
    """
    Create a profile by username with data from data broker. Uses db as cache.

    Args:
        link: The LinkedIn profile link or username
        user: Optional authenticated user
        turnstile_token: The Turnstile verification token
        remote_ip: The IP address of the request

    Returns:
        The created profile
    """
    remote_ip = request.client.host if request.client else None
    username = profile_service.extract_username(username)

    is_authenticated = user is not None

    if is_authenticated:
        return await profile_service.create_profile_for_user_from_remote_data(
            username, user
        )
    else:
        if not turnstile_data.turnstileToken:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ApiErrorType.Unauthorized.value,
            )

        is_verified = await auth_service.verify_turnstile(
            turnstile_data.turnstileToken, remote_ip
        )
        if not is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ApiErrorType.Unauthorized.value,
            )

        return await profile_service.create_guest_profile_from_remote_data(username)


@profile_controller_v1.patch("/{username}")
@handle_exceptions()
async def update_profile(
    username: str,
    profile_data: UpdateProfile,
    profile_service: ProfileServiceDep,
    user: OptionalCurrentUserDep,
):
    return await profile_service.update_profile(username, profile_data, user)


# REQUIRED AUTH ROUTES
@profile_controller_v1.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions()
async def delete_profile(
    username: str,
    profile_service: ProfileServiceDep,
    user: CurrentUserDep,
):
    """
    Delete a profile.
    Requires authentication. Only the owner of the profile can delete it.
    """
    return await profile_service.delete_profile(username, user)


@profile_controller_v1.patch("/{username}/publish")
@handle_exceptions()
async def publish_profile(
    username: str,
    profile_data: PublishingOptionsUpdate,
    profile_service: ProfileServiceDep,
    user: CurrentUserDep,
):
    return await profile_service.publish_profile(username, profile_data, user)


@profile_controller_v1.patch("/{username}/unpublish")
@handle_exceptions()
async def unpublish_profile(
    username: str,
    profile_service: ProfileServiceDep,
    user: CurrentUserDep,
):
    """
    Unpublish a profile.
    Requires authentication. Only the owner of the profile can unpublish it.
    """
    return await profile_service.unpublish_profile(username, user)


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
