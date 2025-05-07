from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import (
    HTTPException as FastAPIHTTPException,
)
from fastapi.exceptions import (
    RequestValidationError as FastAPIRequestValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.core.exceptions import (
    HTTPException,
    HTTPExceptionType,
    RequestValidationException,
    UncaughtException,
)
from src.core.interfaces import ILogger


def get_invalid_input_error_message(message: str, parameter: str | None = None) -> str:
    return f"Invalid input{' parameter: ' + parameter if parameter else ''}. {message}"


def add_exception_handlers(app: FastAPI, logger: ILogger) -> None:

    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(
        request: Request, exc: HTTPException, logger=logger
    ):
        logger.error(
            f"HTTPException{f' in {exc.origin}' if exc.origin else ''}: {exc.status_code} - {exc.detail}"
        )
        return await http_exception_handler(
            request,
            FastAPIHTTPException(
                status_code=exc.status_code,
                detail=exc.detail,
                headers=exc.headers,
            ),
        )

    @app.exception_handler(UncaughtException)
    async def uncaught_exception_handler(
        request: Request, exc: UncaughtException, logger=logger
    ):
        logger.error(f"Unhandled exception in {exc.origin}: {exc.detail}")
        return await http_exception_handler(
            request,
            FastAPIHTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=HTTPExceptionType.InternalServerError.value,
            ),
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded, logger=logger
    ):
        logger.error(f"Rate limit exceeded: {exc}")
        return _rate_limit_exceeded_handler(request, exc)

    @app.exception_handler(FastAPIRequestValidationError)
    async def request_validation_error_handler(
        request: Request, exc: FastAPIRequestValidationError, logger=logger
    ):
        logger.error(f"Request is not valid: {exc}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                {
                    "detail": [
                        get_invalid_input_error_message(error["msg"], error["loc"][-1])
                        for error in exc.errors()
                    ],
                    **(
                        {"body": request.body}
                        if hasattr(request, "body") and request.body
                        else {}
                    ),
                }
            ),
        )

    @app.exception_handler(RequestValidationException)
    async def request_validation_exception_handler(
        request: Request, exc: RequestValidationException, logger=logger
    ):
        logger.error(f"Request is not valid: {exc}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                {
                    "detail": get_invalid_input_error_message(
                        exc.message, exc.parameter
                    ),
                    **(
                        {"body": request.body}
                        if hasattr(request, "body") and request.body
                        else {}
                    ),
                }
            ),
        )
