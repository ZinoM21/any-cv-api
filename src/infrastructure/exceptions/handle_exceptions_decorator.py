import inspect
from functools import wraps
from typing import (
    Optional,
    TypeVar,
)

from fastapi.exceptions import HTTPException, RequestValidationError

from src.infrastructure.exceptions import (
    HTTPExceptionWithOrigin,
    UnauthorizedHTTPException,
    UncaughtException,
)

T = TypeVar("T")


def handle_exceptions(origin: Optional[str] = None):
    """
    Decorator that handles exceptions in controller endpoints.
    Works with both synchronous and asynchronous functions.

    Args:
        origin: The origin of the exception for proper error reporting.
               If not provided, it will be inferred from the function name.

    Returns:
        Decorated function
    """

    def get_exception_origin(func):
        if origin is not None:
            return origin
        module_name = func.__module__.split(".")[-1]
        function_name = func.__name__
        return f"{module_name}.{function_name}"

    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                exception_origin = get_exception_origin(func)

                try:
                    return await func(*args, **kwargs)
                except (RequestValidationError,):
                    # Re-raise these exceptions directly
                    raise
                except (HTTPException, UnauthorizedHTTPException) as exc:
                    # Add an origin to HTTPExceptions
                    raise HTTPExceptionWithOrigin(
                        status_code=exc.status_code,
                        detail=exc.detail,
                        origin=exception_origin,
                    )
                except (Exception, UncaughtException) as exc:
                    # All other exceptions are considered uncaught
                    raise UncaughtException(origin=exception_origin, detail=str(exc))

            return async_wrapper

        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                exception_origin = get_exception_origin(func)

                try:
                    return func(*args, **kwargs)
                except (
                    UnauthorizedHTTPException,
                    HTTPException,
                    RequestValidationError,
                ):
                    # Re-raise these exceptions directly
                    raise
                except (Exception, UncaughtException) as e:
                    # All other exceptions are considered uncaught
                    raise UncaughtException(origin=exception_origin, detail=str(e))

            return sync_wrapper

    return decorator
