from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.decorators import handle_exceptions
from src.core.domain.models import UpdateProfile
from src.deps import LoggerDep, ProfileServiceDep


class ProfileInfoRequest(BaseModel):
    link: str


profile_controller_v1 = APIRouter(prefix="/v1/profile")


@profile_controller_v1.get("/healthz")
async def healthz():
    return JSONResponse(content={"status": "ok"})


@profile_controller_v1.get("/{username}")
@handle_exceptions()
async def get_profile(
    username: str, profile_service: ProfileServiceDep, logger: LoggerDep
):
    profile = await profile_service.get_profile(username)
    return JSONResponse(content=profile)


@profile_controller_v1.patch("/{username}")
@handle_exceptions()
async def update_profile(
    username: str,
    profile_data: UpdateProfile,
    profile_service: ProfileServiceDep,
):
    """Update a user profile with partial data"""
    updated_profile = await profile_service.update_profile(username, profile_data)
    return JSONResponse(content=updated_profile)


@profile_controller_v1.get("/info/{username}")
@handle_exceptions()
async def profile_info(
    username: str,
    profile_service: ProfileServiceDep,
) -> JSONResponse:
    """Get profile info based on the username"""
    profile_data = await profile_service.get_profile_info(username)
    return JSONResponse(content=profile_data)
