from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.interfaces.dtos import ProfileInfoRequest
from src.useCases.services.profile_service import ProfileService
from src.config.logger import logger

router = APIRouter()


class ProfileController:
    def __init__(self, profile_service: ProfileService):
        self.profile_service = profile_service

    async def get_profile_info(self, request: ProfileInfoRequest) -> JSONResponse:
        try:
            profile_data = await self.profile_service.get_profile_info(request.link)
            return JSONResponse(content=profile_data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Controller error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
