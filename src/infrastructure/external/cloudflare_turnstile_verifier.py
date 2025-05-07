from fastapi import status

from src.config import Settings
from src.core.exceptions import (
    HTTPException,
    HTTPExceptionType,
    RequestValidationException,
    handle_exceptions,
)
from src.core.interfaces import ILogger, ITurnstileVerifier

from .base_api_adapter import BaseApiAdapter


class CloudflareTurnstileVerifier(BaseApiAdapter, ITurnstileVerifier):
    def __init__(
        self,
        logger: ILogger,
        settings: Settings,
        secret: str | None = None,
    ):
        super().__init__(
            logger=logger, settings=settings, base_url=settings.TURNSTILE_CHALLENGE_URL
        )
        self.secret_key = secret or settings.TURNSTILE_SECRET_KEY

    @handle_exceptions()
    async def verify_token(
        self, token: str | None, remote_ip: str | None = None
    ) -> bool:
        """
        Verify a Turnstile token against an external service.

        Args:
            token: The token to verify
            remote_ip: Optional IP address of the user

        Returns:
            True if verification was successful

        Raises:
            HTTPException: If verification fails
        """
        if not token:
            raise RequestValidationException(
                message="Turnstile token is required",
                parameter="turnstileToken",
            )

        data = {
            "secret": self.secret_key,
            "response": token,
        }

        if remote_ip:
            data["remoteip"] = remote_ip

        response = await self.post(json_data=data)

        if not response:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=HTTPExceptionType.ServiceUnavailable.value,
            )

        if not response.get("success"):
            error_codes = response.get("error-codes") or []
            self.logger.error(f"Turnstile verification failed: {error_codes}")

            if "missing-input-response" in error_codes or "bad-request" in error_codes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=HTTPExceptionType.BadRequest.value,
                )
            elif (
                "invalid-input-response" in error_codes
                or "timeout-or-duplicate" in error_codes
            ):
                raise RequestValidationException(
                    message="Turnstile token is invalid",
                    parameter="turnstileToken",
                )
            elif "internal-error" in error_codes:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=HTTPExceptionType.ServiceUnavailable.value,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=HTTPExceptionType.InternalServerError.value,
                )

        self.logger.debug("Request validated against Turnstile")
        return True
