from typing import Dict, List, Optional, Union

import resend
from fastapi import status

from src.config import Settings
from src.core.dtos import Attachment, Email, Tag
from src.core.exceptions import (
    HTTPException,
    HTTPExceptionType,
    handle_exceptions,
)
from src.core.interfaces import IEmailService, ILogger


class ResendEmailService(IEmailService):
    """Email service that uses Resend API to send emails."""

    def __init__(self, logger: ILogger, settings: Settings):
        """Initialize the Resend email service.

        Args:
            logger: Logger instance
            settings: Application settings
        """
        self.logger = logger
        self.settings = settings
        self.frontend_url = settings.FRONTEND_URL
        self.email_from = settings.RESEND_FROM_EMAIL
        self.email_to = settings.RESEND_TO_EMAIL

        resend.api_key = settings.RESEND_API_KEY

    @handle_exceptions()
    async def _send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        cc: Optional[Union[List[str], str]] = None,
        bcc: Optional[Union[List[str], str]] = None,
        reply_to: Optional[Union[List[str], str]] = None,
        attachments: Optional[List[Attachment]] = None,
        tags: Optional[List[Tag]] = None,
        headers: Optional[Dict[str, str]] = None,
        scheduled_at: Optional[str] = None,
    ) -> Email:
        """Send a general email using Resend.

        Args:
            to_email: The recipient's email address
            subject: The email subject
            html_content: The HTML content of the email
            text_content: Optional plain text content
            cc: Optional string or list of CC recipients
            bcc: Optional string or list of BCC recipients
            reply_to: Optional string or list of reply-to email address
            attachments: Optional list of attachments
            tags: Optional list of tags
            headers: Optional dictionary of headers
            scheduled_at: Optional date and time to schedule the email

        Returns:
            Email: The email object
        Raises:
            HTTPException 500: If the email fails to send
        """

        params: resend.Emails.SendParams = {
            "from": f"Zino from BuildAnyCV <{self.email_from}>",
            "to": self.email_to or to_email,
            "subject": subject,
        }

        optional_params = {
            "html": html_content,
            "text": text_content,
            "cc": cc,
            "bcc": bcc,
            "reply_to": reply_to,
            "attachments": attachments,
            "tags": tags,
            "headers": headers,
            "scheduled_at": scheduled_at,
        }

        for k, v in optional_params.items():
            if v is not None:
                params[k] = v

        try:
            return resend.Emails.send(params)

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=HTTPExceptionType.InternalServerError.value,
            )

    @handle_exceptions()
    async def send_verification_email(
        self, email: str, token: str, name: str = ""
    ) -> Email:
        """Send a verification email to a newly registered user.

        Args:
            email: The recipient's email address
            token: The verification token
            name: The recipient's name

        Returns:
            Email: The email object if sent successfully
        """
        verification_url = f"{self.frontend_url}/verify-email?token={token}"

        html_content = f"""
            <div>
                <h2>Welcome to Any CV, {name}!</h1>
                <p>Thank you for signing up. To complete your registration, please verify your email address by clicking the button below:</p>
                <div>
                <a href="{verification_url}" style="display: inline-block; background-color: #4F46E5; color: #FFFFFF; font-weight: 600; padding: 0.5rem 1rem; border-radius: 0.375rem; text-decoration: none;">
                    Verify Email Address
                </a>
            </div>
            <p>If you didn't create an account, you can safely ignore this email.</p>
            <p>This link will expire in {self.settings.EMAIL_VERIFICATION_EXPIRES_IN_HOURS} hours.</p>

            <p>Best regards,</p>
            <p>Zino from BuildAnyCV</p>

            
            <div style="margin-top: 20px;">
                <p>Copyright © 2025 BuildAnyCV</p>
            </div>

            <span style="font-size: 10px; color: #6B7280;">
                This email was sent to {email}
            </span>
        </div>
        """

        verification_email = await self._send_email(
            to_email=email,
            subject="Confirm your BuildAnyCV account",
            html_content=html_content,
        )
        self.logger.debug(f"Verification email sent to {email}.")
        return verification_email

    @handle_exceptions()
    async def send_password_reset_email(
        self, email: str, token: str, name: str = ""
    ) -> Email:
        """Send a password reset email to a user.

        Args:
            email: The recipient's email address
            token: The password reset token
            name: The recipient's name

        Returns:
            Email: The email object if sent successfully
        """
        reset_url = f"{self.frontend_url}/reset-password?token={token}"

        html_content = f"""
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <tr>
                    <td style="padding: 20px;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                                <td style="padding-bottom: 20px;">
                                    <h2 style="margin: 0; color: #111827;">Reset Your Password, {name}</h2>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 20px;">
                                    <p style="margin: 0; color: #4B5563;">We received a request to reset your password. Click the button below to create a new password:</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 20px;">
                                    <table cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td style="background-color: #4F46E5; border-radius: 6px; padding: 10px 16px;">
                                                <a href="{reset_url}" style="color: #FFFFFF; text-decoration: none; font-weight: 600; display: inline-block;">Reset Password</a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 10px;">
                                    <p style="margin: 0; color: #4B5563;">If you didn't request a password reset, you can safely ignore this email.</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 20px;">
                                    <p style="margin: 0; color: #4B5563;">This link will expire in {self.settings.EMAIL_VERIFICATION_EXPIRES_IN_HOURS} hours.</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 10px;">
                                    <p style="margin: 0; color: #4B5563;">Best regards,</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 20px;">
                                    <p style="margin: 0; color: #4B5563;">Zino from BuildAnyCV</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="border-top: 1px solid #E5E7EB; padding-top: 20px;">
                                    <p style="margin: 0; color: #6B7280; font-size: 12px;">Copyright © 2025 BuildAnyCV</p>
                                    <p style="margin: 6px 0 0; color: #6B7280; font-size: 10px;">This email was sent to {email}</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        """

        text_content = f"""
        Reset Your Password, {name}
        
        We received a request to reset your password. Please visit the link below to create a new password:
        
        {reset_url}
        
        If you didn't request a password reset, you can safely ignore this email.
        
        This link will expire in {self.settings.EMAIL_VERIFICATION_EXPIRES_IN_HOURS} hours.
        
        Best regards,
        Zino from BuildAnyCV
        
        Copyright © 2025 BuildAnyCV
        This email was sent to {email}
        """

        reset_email = await self._send_email(
            to_email=email,
            subject="Reset Your BuildAnyCV Password",
            html_content=html_content,
            text_content=text_content,
        )
        self.logger.debug(f"Password reset email sent to {email}.")
        return reset_email
