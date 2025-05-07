from contextlib import asynccontextmanager
from typing import Type

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from src.config import Settings
from src.core.interfaces import ILogger
from src.deps import (
    Database,
    get_settings,
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


# Init App
def build_app(
    db: Type[Database] = Database,
    settings: Settings = get_settings(),
    app_logger: ILogger = logger,
):
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        """Context manager to handle application lifespan events"""
        app_logger.info("FastAPI application started")
        try:
            db.connect(settings.MONGODB_URL, app_logger)
            yield

        except Exception as e:
            app_logger.error(f"Application startup failed: {str(e)}")
            raise

        finally:
            db.disconnect(app_logger)

    app = FastAPI(
        root_path="/api",
        title="AnyCV API",
        description="API for AnyCV application",
        version="1.0.0",
        lifespan=app_lifespan,
    )

    # Limits
    app.state.limiter = limiter

    # Exception Handlers
    add_exception_handlers(app, app_logger)

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
        return {"status": "ok"}

    return app


app = build_app()
