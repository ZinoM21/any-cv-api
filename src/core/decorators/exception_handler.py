from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar

from fastapi.exceptions import HTTPException, RequestValidationError

from src.core.exceptions import UncaughtException

T = TypeVar("T")


def handle_exceptions(origin: Optional[str] = None):
    """
    Decorator that handles exceptions in controller endpoints.

    Args:
        origin: The origin of the exception for proper error reporting.
               If not provided, it will be inferred from the function name.

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            exception_origin = origin
            # Get the module name and function name as origin if not provided
            if exception_origin is None:
                module_name = func.__module__.split(".")[-1]
                function_name = func.__name__
                exception_origin = f"{module_name}.{function_name}"

            try:
                return await func(*args, **kwargs)
            except (HTTPException, RequestValidationError, UncaughtException):
                # Re-raise these exceptions directly
                raise
            except Exception as e:
                # All other exceptions are considered uncaught
                raise UncaughtException(origin=exception_origin, detail=str(e))

        return wrapper

    return decorator
