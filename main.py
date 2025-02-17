from typing import Union

import os
import re
import requests
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from loguru import logger

from models import CVRequest

# Configure logger
logger.add(
    "logs/api.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
)

load_dotenv()

app = FastAPI()
logger.info("FastAPI application started")

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
def get_cv(request: CVRequest):
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

        if response.status_code != 200:
            logger.error(
                f"RapidAPI request failed with status code: {response.status_code}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch data from RapidAPI",
            )

        logger.info(f"Successfully retrieved CV data for user: {username}")
        return response.json()

    except requests.RequestException as req_err:
        logger.exception(f"Request error while processing request: {str(req_err)}")
        raise HTTPException(
            status_code=500, detail="Internal server error: Request failed"
        )

    except Exception as e:
        logger.exception(f"Unexpected error while processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
