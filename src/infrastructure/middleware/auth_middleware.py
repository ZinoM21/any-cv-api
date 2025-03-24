from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.core.exceptions import UnauthorizedHTTPException


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in settings.public_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await http_exception_handler(
                request,
                UnauthorizedHTTPException(
                    detail="Missing or invalid authorization header"
                ),
            )

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token, settings.nextauth_secret, algorithms=[settings.auth_algorithm]
            )

            user_id = payload.get("sub")
            if user_id is None:
                return await http_exception_handler(
                    request, UnauthorizedHTTPException(detail="Invalid token")
                )

            request.state.user = {"user_id": user_id}
            return await call_next(request)

        except JWTError:
            return await http_exception_handler(
                request, UnauthorizedHTTPException(detail="Invalid token")
            )
