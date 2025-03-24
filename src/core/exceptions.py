from fastapi import HTTPException, status


class UncaughtException(Exception):
    """Exception for uncaught exceptions"""

    def __init__(self, origin: str, detail: str | None = None) -> None:
        super().__init__(detail)
        if detail is None:
            self.origin = "unknown origin"
            self.detail = origin
        else:
            self.origin = origin
            self.detail = detail


class UnauthorizedHTTPException(HTTPException):
    """Exception for unauthorized access"""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
