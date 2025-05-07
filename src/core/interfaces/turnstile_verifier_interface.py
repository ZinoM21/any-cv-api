from abc import ABC, abstractmethod


class ITurnstileVerifier(ABC):
    """Interface for turnstile verification."""

    @abstractmethod
    async def verify_token(
        self, token: str | None, remote_ip: str | None = None
    ) -> bool:
        """
        Verify a turnstile token.

        Args:
            token: The token to verify
            remote_ip: Optional IP address of the user

        Returns:
            True if verification was successful
        """
        pass
