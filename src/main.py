from typing import Union
import os
import re
import requests
import time
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .interfaces.dtos.request import ProfileInfoRequest
from .interfaces.middleware.cors import setup_cors_middleware
from .infrastructure.database.database import Database
from .config.logger import logger
from .config.environment import env

from .infrastructure.external.linkedin_api import LinkedInAPI
from .infrastructure.persistence.profile_repository import ProfileRepository
from .useCases.services.profile_service import ProfileService

app = FastAPI()
logger.info("FastAPI application started")

setup_cors_middleware(app)

# Dependencies
linkedin_api = LinkedInAPI()
profile_repository = ProfileRepository()
profile_service = ProfileService(profile_repository, linkedin_api)


@app.on_event("startup")
async def startup_event():
    """Initialize all application resources and middleware on startup"""
    try:
        # 1. Validate environment
        env.validate()
        logger.info("Environment variables validated successfully")

        # 2. Initialize database connection
        await Database.connect()

    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    await Database.disconnect()


@app.get("/")
def read_root():
    logger.debug("Root endpoint accessed")
    return {"Hello": "World"}


@app.post("/profile-info")
async def profile_info(request: ProfileInfoRequest):
    try:
        profile_data = await profile_service.get_profile_info(request.link)
        return JSONResponse(content=profile_data)

    except ValueError as e:
        logger.error(f"Controller error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Controller error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Add new endpoints using Beanie's features
# @app.get("/profiles/{username}")
# async def get_profile(username: str):
#     profile = await Profile.find_one(Profile.linkedin_username == username)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Profile not found")
#     return profile


# @app.get("/profiles")
# async def list_profiles(skip: int = 0, limit: int = 10):
#     profiles = await Profile.find_all().skip(skip).limit(limit).to_list()
#     return profiles
