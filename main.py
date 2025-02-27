from typing import Union
import os
import re
import requests
import time
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

from models import ProfileInfoRequest, Profile
from transformers.linkedin import create_profile_from_linkedin_data
from database import Database

logger = logging.getLogger("uvicorn")


load_dotenv()

app = FastAPI()
logger.info("FastAPI application started")

@app.on_event("startup")
async def startup_db_client():
    await Database.connect()
    logger.info("Connected to MongoDB")


@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.disconnect()
    logger.info("Disconnected from MongoDB")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware enabled")


@app.get("/")
def read_root():
    logger.debug("Root endpoint accessed")
    return {"Hello": "World"}


@app.post("/profile-info")
async def get_cv(request: ProfileInfoRequest):
    logger.info(f"Processing CV request for URL: {request.link}")

    # Extract username from URL or use direct username
    username = request.link.strip()

    # If it's a URL, extract the username
    if "/" in username:
        # Match LinkedIn URLs in various formats
        match = re.match(
            r"^(?:https?:\/\/)?(?:[\w]+\.)?linkedin\.com\/in\/([\w\-]+)\/?.*$", username
        )

        if not match:
            logger.warning(f"Invalid LinkedIn URL received: {request.link}")
            raise HTTPException(
                status_code=400,
                detail="Invalid LinkedIn URL. Must be a LinkedIn profile URL (/in/) or just the username",
            )

        username = match.group(1)

    else:
        # Validate username format when provided directly
        if not re.match(r"^[\w\-]+$", username):
            logger.warning(f"Invalid username format: {request.link}")
            raise HTTPException(status_code=400, detail="Invalid username format")

    logger.debug(f"Extracted username: {username}")

    # Check if profile already exists in DB
    profile = await Profile.find_one(Profile.username == username)
    if profile:
        logger.debug(f"Profile data found in MongoDB for user: {username}")
        return JSONResponse(content=json.loads(profile.json(exclude={"id": True})))

    try:
        # Fetch data from RapidAPI
        rapidapi_url = os.getenv("RAPIDAPI_URL")
        rapidapi_host = os.getenv("RAPIDAPI_HOST")
        rapidapi_key = os.getenv("RAPIDAPI_KEY")
        rapidapi_url = os.getenv("RAPIDAPI_URL")

        if (
            not rapidapi_url
            or not rapidapi_host
            or not rapidapi_key
            or not rapidapi_url
        ):
            logger.error("Missing environment variables for RapidAPI")
            raise HTTPException(
                status_code=500, detail="Internal server error: Missing configuration"
            )

        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        }
        payload = {"link": f"https://www.linkedin.com/in/{username}"}

        logger.debug(f"Making request to RapidAPI for user: {username}")
        response = requests.post(rapidapi_url, json=payload, headers=headers)

        if response.status_code == 404:
            logger.error(
                f"RapidAPI request failed with status code: {response.status_code}"
            )
            return JSONResponse(content={"error": "User not found"}, status_code=404)

        if response.status_code != 200:
            logger.error(
                f"RapidAPI request failed with status code: {response.status_code}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch data from RapidAPI",
            )

        logger.debug(f"Successfully retrieved CV data for user: {username}")


        logger.info(f"Successfully retrieved CV data for user: {username}")

        profile = create_profile_from_linkedin_data(response_data)
        await profile.create()
        logger.debug(f"Saved profile data to MongoDB for user: {username}")

        return JSONResponse(content=json.loads(profile.json(exclude={"id": True})))

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Failed to fetch data for user: {username}")
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
