from typing import Dict, Optional

from .exception_types import HTTPExceptionType


class UncaughtException(Exception):
    """Exception for uncaught exceptions"""

    def __init__(self, origin: str, detail: str) -> None:
        super().__init__(detail)
        self.origin = origin
        self.detail = detail


class DataTransformerError(Exception):
    """Base exception for DataTransformer errors."""

    pass


class DataValidationError(DataTransformerError):
    """Raised when data validation fails."""

    pass


class RequestValidationException(Exception):
    """Raised when request validation fails."""

    def __init__(self, message: str, parameter: str | None = None) -> None:
        self.message = message
        self.parameter = parameter


class HTTPException(Exception):
    """Exception for HTTP exceptions"""

    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.headers = headers


class UnauthorizedHTTPException(HTTPException):
    """Exception for unauthorized access"""

    def __init__(
        self,
        detail: str | None = HTTPExceptionType.Unauthorized.value,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(status_code=401, detail=detail, headers=headers)


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
