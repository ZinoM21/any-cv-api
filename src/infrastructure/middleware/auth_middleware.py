from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from src.deps import settings
from src.infrastructure.exceptions.exceptions import UnauthorizedHTTPException


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None

        is_protected_route = not any(
            request.url.path.startswith(excluded)
            for excluded in settings.all_public_paths
        )
        auth_header = request.headers.get("Authorization")
        has_bearer_token = auth_header and auth_header.startswith("Bearer ")

        if is_protected_route and not has_bearer_token:
            return await http_exception_handler(
                request,
                UnauthorizedHTTPException(
                    detail="Missing or invalid authorization header"
                ),
            )

        if auth_header and has_bearer_token:
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    token, settings.auth_secret, algorithms=[settings.auth_algorithm]
                )
                user_id = payload.get("sub")
                if user_id:
                    # Set user info in request state
                    request.state.user = {"user_id": user_id}

                # For protected routes, require valid user_id
                if not user_id and is_protected_route:
                    return await http_exception_handler(
                        request, UnauthorizedHTTPException(detail="Invalid token")
                    )

            except JWTError as e:
                if "expired" in str(e):
                    return await http_exception_handler(
                        request, UnauthorizedHTTPException(detail="Token expired")
                    )
                # For protected routes, return error on invalid token
                if is_protected_route:
                    return await http_exception_handler(
                        request, UnauthorizedHTTPException(detail="Invalid token")
                    )

        return await call_next(request)
