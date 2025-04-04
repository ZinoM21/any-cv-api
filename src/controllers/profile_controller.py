from fastapi import APIRouter
from pydantic import BaseModel

from src.core.domain.models import UpdateProfile
from src.deps import OptionalCurrentUserDep, ProfileServiceDep
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class ProfileInfoRequest(BaseModel):
    link: str


profile_controller_v1 = APIRouter(prefix="/v1/profile", tags=["profile"])


@profile_controller_v1.get("/healthz")
async def healthz():
    return {"status": "ok"}


@profile_controller_v1.get("/{username}")
@handle_exceptions()
async def get_profile(
    username: str,
    profile_service: ProfileServiceDep,
    user: OptionalCurrentUserDep,
):
    return await profile_service.get_profile(username, user)


@profile_controller_v1.post("/{username}")
@handle_exceptions()
async def create_profile(
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
