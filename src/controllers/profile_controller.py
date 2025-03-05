from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.deps import get_profile_service, get_logger, LoggerDep
from src.useCases.services import IProfileService


class ProfileInfoRequest(BaseModel):
    link: str


profile_controller = APIRouter()


@profile_controller.post("/profile-info")
async def profile_info(
    request: ProfileInfoRequest,
    profile_service: Annotated[IProfileService, Depends(get_profile_service)],
    logger: LoggerDep,
) -> JSONResponse:
    try:
        profile_data = await profile_service.get_profile_info(request.link)
        return JSONResponse(content=profile_data)

    # TODO: catch the correct erros here: e.g. what RequestValidationError if link is not in the request
    # see https://fastapi.tiangolo.com/tutorial/handling-errors/#override-the-default-exception-handlers
    except ValueError as e:
        logger.error(f"Controller error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Controller error: {str(e)}")
        logger.error(type(e))
        raise HTTPException(status_code=500, detail="Internal server error")
