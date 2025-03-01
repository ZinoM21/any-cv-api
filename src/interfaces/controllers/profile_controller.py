from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.config import logger
from src.interfaces.dtos import ProfileInfoRequest

from src.infrastructure.external import LinkedInAPI
from src.infrastructure.persistence import ProfileRepository

from src.useCases.services import ProfileService

# Dependencies
linkedin_api = LinkedInAPI()
profile_repository = ProfileRepository()
profile_service = ProfileService(profile_repository, linkedin_api)


def get_profile_service() -> ProfileService:
    return profile_service


router = APIRouter()


@router.post("/profile-info")
async def profile_info(
    request: ProfileInfoRequest,
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> JSONResponse:
    try:
        profile_data = await profile_service.get_profile_info(request.link)
        return JSONResponse(content=profile_data)

    except ValueError as e:
        logger.error(f"Controller error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Controller error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
