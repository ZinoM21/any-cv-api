from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from src.config import env
from src.config import logger


def setup_cors_middleware(app: FastAPI) -> None:
    """
    Configure and add CORS middleware to the FastAPI application.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[env.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware enabled")
