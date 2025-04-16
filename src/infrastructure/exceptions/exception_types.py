from enum import Enum


class ApiErrorType(Enum):
    Unauthorized = "unauthorized"
    Forbidden = "forbidden"
    TokenExpired = "token_expired"
    InvalidToken = "invalid_token"
    InvalidCredentials = "invalid_credentials"
    ResourceNotFound = "resource_not_found"
    ResourceAlreadyExists = "resource_already_exists"
    ServiceUnavailable = "service_unavailable"
