from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.controllers import (
    auth_controller_v1,
    file_controller_v1,
    profile_controller_v1,
)
from src.deps import Database, logger, settings
from src.infrastructure.exceptions.add_exception_handlers import add_exception_handlers
from src.infrastructure.middleware import AuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI, logger=logger, db=Database):
    """Context manager to handle application lifespan events"""
    logger.info("FastAPI application started")
    try:
        await db.connect(logger)
        yield

    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise

    finally:
        await db.disconnect(logger)


# Init App
app = FastAPI(
    root_path="/api",
    title="AnyCV API",
    description="API for AnyCV application",
    version="0.1.0",
    lifespan=lifespan,
)


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

# Exception Handlers
add_exception_handlers(app, logger)


# Controllers / routes
app.include_router(profile_controller_v1)
app.include_router(file_controller_v1)
app.include_router(auth_controller_v1)


@app.get("/healthz")
async def healthz():
    return JSONResponse(content={"status": "ok"})
