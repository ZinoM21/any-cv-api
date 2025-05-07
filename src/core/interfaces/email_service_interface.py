from abc import ABC, abstractmethod

from ..dtos import Email


class IEmailService(ABC):
    """Interface for email service implementations."""

    @abstractmethod
    async def send_verification_email(
        self, email: str, token: str, name: str = ""
    ) -> Email | None:
        """Send a verification email to a user.

        Args:
            email: The recipient's email address
            token: The verification token
            name: The recipient's name

        Returns:
            bool: True if the email was sent successfully
        """
        pass

    @abstractmethod
    async def send_password_reset_email(
        self, email: str, token: str, name: str = ""
    ) -> Email | None:
        """Send a password reset email to a user.

        Args:
            email: The recipient's email address
            token: The password reset token
            name: The recipient's name

        Returns:
            Email: The email object if sent successfully
        """
        pass
