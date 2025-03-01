from typing import Union
import os
import re
import requests
import time
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .config import env
from .config import logger

from .interfaces.dtos.request import ProfileInfoRequest
from .interfaces.middleware.cors import setup_cors_middleware
from .interfaces.controllers import profile_controller

from .infrastructure.database.database import Database

app = FastAPI(
    root_path="/api/v1",
    title="AnyCV API",
    description="API for AnyCV application",
    version="0.1.0",
)
logger.info("FastAPI application started")

# Middleware
setup_cors_middleware(app)

# Controllers / routes
app.include_router(profile_controller.router)


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
