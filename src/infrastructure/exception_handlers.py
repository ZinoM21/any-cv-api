from fastapi import FastAPI
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.core.domain.interfaces import ILogger
from src.core.exceptions import UnauthorizedHTTPException, UncaughtException


def add_exception_handlers(app: FastAPI, logger: ILogger) -> None:
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(
        request: Request, exc: HTTPException, logger=logger
    ):
        logger.error(f"HTTPException: {exc}")
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def custom_request_validation_exception_handler(
        request: Request, exc: RequestValidationError, logger=logger
    ):
        logger.error(f"RequestValidationError: {exc}")
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(UncaughtException)
    async def uncaught_exception_handler(
        request: Request, exc: UncaughtException, logger=logger
    ):
        logger.error(f"Unhandled exception in {exc.origin}: {exc.detail}")
        headers = getattr(exc, "headers", None)
        return JSONResponse(
            {"detail": "Internal Server error"}, status_code=500, headers=headers
        )
