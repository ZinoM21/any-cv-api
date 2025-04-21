from fastapi import HTTPException, status

from .exception_types import ApiErrorType


class UncaughtException(Exception):
    """Exception for uncaught exceptions"""

    def __init__(self, origin: str, detail: str) -> None:
        super().__init__(detail)
        self.origin = origin
        self.detail = detail


class UnauthorizedHTTPException(HTTPException):
    """Exception for unauthorized access"""

    def __init__(self, detail: str | None = ApiErrorType.Unauthorized.value) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class HTTPExceptionWithOrigin(HTTPException):
    """Exception for HTTP exceptions with an origin"""

    def __init__(
        self, status_code: int, origin: str, detail: str | None = None
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail=detail,
        )
        self.origin = origin
