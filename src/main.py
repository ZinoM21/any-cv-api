from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware

from src.config import settings
from src.deps import (
    Database,
    limiter,
    logger,
)
from src.presentation.controllers import (
    auth_controller_v1,
    file_controller_v1,
    profile_controller_v1,
    user_controller_v1,
)
from src.presentation.exceptions import add_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI, logger=logger, db=Database):
    """Context manager to handle application lifespan events"""
    logger.info("FastAPI application started")
    try:
        db.connect(logger)
        yield

    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise

    finally:
        db.disconnect(logger)


# Init App
app = FastAPI(
    root_path="/api",
    title="AnyCV API",
    description="API for AnyCV application",
    version="1.0.0",
    lifespan=lifespan,
)


# Limits
app.state.limiter = limiter


# Exception Handlers
add_exception_handlers(app, logger)


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)


# Controllers / routes
app.include_router(profile_controller_v1)
app.include_router(file_controller_v1)
app.include_router(auth_controller_v1)
app.include_router(user_controller_v1)


@app.get("/healthz")
async def healthz():
    return JSONResponse(content={"status": "ok"})
