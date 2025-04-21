from fastapi import FastAPI, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.core.domain.interfaces import ILogger

from .exceptions import (
    ApiErrorType,
    HTTPExceptionWithOrigin,
    UncaughtException,
)


def add_exception_handlers(app: FastAPI, logger: ILogger) -> None:

    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(
        request: Request, exc: HTTPException, logger=logger
    ):
        logger.error(f"HTTPException: {exc}")
        return await http_exception_handler(request, exc)

    @app.exception_handler(HTTPExceptionWithOrigin)
    async def custom_http_exception_with_origin_handler(
        request: Request, exc: HTTPExceptionWithOrigin, logger=logger
    ):
        logger.error(f"HTTPException in {exc.origin}: {exc.detail}")
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
            {"detail": ApiErrorType.InternalServerError.value},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers=headers,
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded, logger=logger
    ):
        logger.error(f"Rate limit exceeded: {exc}")
        return _rate_limit_exceeded_handler(request, exc)
