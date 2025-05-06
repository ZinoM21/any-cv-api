from enum import Enum


class HTTPExceptionType(Enum):
    BadRequest = "bad_request"
    Unauthorized = "unauthorized"
    Forbidden = "forbidden"
    TokenExpired = "token_expired"
    InvalidToken = "invalid_token"
    InvalidCredentials = "invalid_credentials"
    ResourceNotFound = "resource_not_found"
    ResourceAlreadyExists = "resource_already_exists"
    ServiceUnavailable = "service_unavailable"
    InternalServerError = "internal_server_error"
