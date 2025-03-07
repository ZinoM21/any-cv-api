from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.decorators import handle_exceptions
from src.deps import LoggerDep, ProfileServiceDep


class ProfileInfoRequest(BaseModel):
    link: str


profile_controller = APIRouter()


@profile_controller.get("/profile/{username}")
@handle_exceptions()
async def get_profile(
    username: str, profile_service: ProfileServiceDep, logger: LoggerDep
):
    profile = await profile_service.get_profile(username)
    return JSONResponse(content=profile)


@profile_controller.post("/profile-info")
@handle_exceptions()
async def profile_info(
    request: ProfileInfoRequest,
    profile_service: ProfileServiceDep,
    logger: LoggerDep,
) -> JSONResponse:
    profile_data = await profile_service.get_profile_info(request.link)
    return JSONResponse(content=profile_data)
