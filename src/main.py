from typing import Union
import os
import re
import requests
import time
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from .config import env

from src.deps import logger, Database

from src.controllers import profile_controller


@asynccontextmanager
async def lifespan(app: FastAPI, logger=logger, db=Database):
    """Context manager to handle application lifespan events"""
    logger.info("FastAPI application started")
    try:
        # 1. Validate environment
        env.validate()
        logger.info("Environment variables validated successfully")

        # 2. Initialize database connection
        await db.connect(logger)

        yield

    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise

    finally:
        await db.disconnect(logger)


app = FastAPI(
    root_path="/api/v1",
    title="AnyCV API",
    description="API for AnyCV application",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[env.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Controllers / routes
app.include_router(profile_controller)
