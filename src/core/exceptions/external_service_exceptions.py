class ExternalServiceException(Exception):
    """Base exception for external service errors."""

    pass


class ExternalServiceTimeoutException(ExternalServiceException):
    """Exception raised when an external service request times out."""

    pass


class ExternalServiceAuthenticationException(ExternalServiceException):
    """Exception raised when authentication with an external service fails."""

    pass


class ExternalServiceResourceNotFoundException(ExternalServiceException):
    """Exception raised when a resource is not found in an external service."""

    pass


class ProfileServiceException(ExternalServiceException):
    """Exception raised when there's an error with the profile service."""

    pass


class AuthServiceException(ExternalServiceException):
    """Exception raised when there's an error with the auth service."""

    pass
