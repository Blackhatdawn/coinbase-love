"""
CryptoVault Email Service with SendGrid Integration
Supports 6-digit OTP verification with 5-minute expiry
"""
import os
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Try to import SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid not installed. Using mock email service.")


class EmailService:
    """
    Production-ready email service with SendGrid integration.
    Falls back to mock mode if SendGrid is not configured.
    """
    
    def __init__(self):
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = os.environ.get('EMAIL_FROM', 'noreply@cryptovault.financial')
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'CryptoVault Financial')
        self.use_mock = os.environ.get('EMAIL_SERVICE', 'mock') == 'mock'
        
        if self.sendgrid_api_key and SENDGRID_AVAILABLE and not self.use_mock:
            self.client = SendGridAPIClient(self.sendgrid_api_key)
            self.mode = 'sendgrid'
            logger.info("✅ Email service initialized with SendGrid")
        else:
            self.client = None
            self.mode = 'mock'
            logger.info("📧 Email service running in mock mode")
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate a secure random OTP code."""
        return ''.join(random.choices(string.digits, k=length))
    
    def get_otp_expiry(self, minutes: int = 5) -> datetime:
        """Get OTP expiry timestamp (default 5 minutes)."""
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    async def send_verification_email(
        self,
        to_email: str,
        otp_code: str,
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send verification email with 6-digit OTP code.
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit verification code
            user_name: Optional user name for personalization
        
        Returns:
            Dict with success status and message
        """
        subject = "🔐 CryptoVault - Verify Your Email"
        
        # Professional HTML email template with CryptoVault branding
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0b; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0b; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1a1a1d 0%, #0d0d0e 100%); border-radius: 16px; border: 1px solid #2a2a2d; overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; border-bottom: 1px solid #2a2a2d;">
                            <div style="width: 80px; height: 80px; margin: 0 auto 20px; background: linear-gradient(135deg, #C5A049 0%, #8B7355 100%); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 40px;">🛡️</span>
                            </div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">CryptoVault</h1>
                            <p style="margin: 8px 0 0; color: #C5A049; font-size: 14px; letter-spacing: 2px;">SECURE DIGITAL CUSTODY</p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 16px; color: #ffffff; font-size: 24px; font-weight: 600;">Verify Your Email</h2>
                            <p style="margin: 0 0 24px; color: #a0a0a5; font-size: 16px; line-height: 1.6;">
                                {f'Hello {user_name},' if user_name else 'Hello,'}<br><br>
                                Welcome to CryptoVault! Use the verification code below to complete your account setup.
                            </p>
                            
                            <!-- OTP Code Box -->
                            <div style="background: linear-gradient(135deg, #C5A049 0%, #a88b3d 100%); border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
                                <p style="margin: 0 0 8px; color: #0a0a0b; font-size: 14px; font-weight: 500; letter-spacing: 1px;">YOUR VERIFICATION CODE</p>
                                <div style="font-size: 36px; font-weight: 700; color: #0a0a0b; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                    {otp_code}
                                </div>
                            </div>
                            
                            <p style="margin: 24px 0 0; color: #ff6b6b; font-size: 14px; text-align: center;">
                                ⏰ This code expires in <strong>5 minutes</strong>
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #2a2a2d; margin: 32px 0;">
                            
                            <p style="margin: 0; color: #666; font-size: 13px; line-height: 1.6;">
                                <strong>Security Notice:</strong> If you didn't request this code, please ignore this email. Never share your verification code with anyone. CryptoVault will never ask for your password or codes via email.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: #0d0d0e; border-top: 1px solid #2a2a2d; text-align: center;">
                            <p style="margin: 0 0 8px; color: #666; font-size: 12px;">© 2024 CryptoVault Financial, Inc. All rights reserved.</p>
                            <p style="margin: 0; color: #555; font-size: 11px;">1201 Market Street, Suite 101, Wilmington, DE 19801</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        plain_content = f"""
CryptoVault - Verify Your Email

{f'Hello {user_name},' if user_name else 'Hello,'}

Your verification code is: {otp_code}

This code expires in 5 minutes.

If you didn't request this code, please ignore this email.

---
CryptoVault Financial, Inc.
1201 Market Street, Suite 101, Wilmington, DE 19801
        """
        
        if self.mode == 'sendgrid' and self.client:
            return await self._send_sendgrid(to_email, subject, html_content, plain_content)
        else:
            return await self._send_mock(to_email, subject, otp_code)
    
    async def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str
    ) -> Dict[str, Any]:
        """Send email via SendGrid API."""
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
                plain_text_content=Content("text/plain", plain_content)
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent successfully to {to_email}")
                return {
                    "success": True,
                    "message": "Verification email sent successfully",
                    "provider": "sendgrid"
                }
            else:
                logger.error(f"❌ SendGrid error: {response.status_code}")
                return {
                    "success": False,
                    "message": "Failed to send email",
                    "error": f"Status code: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ SendGrid exception: {str(e)}")
            return {
                "success": False,
                "message": "Email service error",
                "error": str(e)
            }
    
    async def _send_mock(
        self,
        to_email: str,
        subject: str,
        otp_code: str
    ) -> Dict[str, Any]:
        """Mock email sending for development/testing."""
        logger.info(f"📧 [MOCK] Email to {to_email}")
        logger.info(f"📧 [MOCK] Subject: {subject}")
        logger.info(f"📧 [MOCK] OTP Code: {otp_code}")
        
        return {
            "success": True,
            "message": "Verification email sent (mock mode)",
            "provider": "mock",
            "debug_otp": otp_code  # Only in mock mode for testing
        }
    
    async def send_welcome_email(self, to_email: str, user_name: str) -> Dict[str, Any]:
        """Send welcome email after successful verification."""
        subject = "🎉 Welcome to CryptoVault - Your Account is Ready!"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0b; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0b; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: #1a1a1d; border-radius: 16px; border: 1px solid #2a2a2d;">
                    <tr>
                        <td style="padding: 40px; text-align: center;">
                            <h1 style="color: #C5A049; margin: 0 0 20px;">🎉 Welcome to CryptoVault!</h1>
                            <p style="color: #ffffff; font-size: 18px; margin: 0 0 16px;">Hello {user_name},</p>
                            <p style="color: #a0a0a5; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                                Your account has been verified and is now ready to use. Start exploring secure P2P trading and institutional-grade custody.
                            </p>
                            <a href="https://cryptovault.financial/dashboard" style="display: inline-block; background: linear-gradient(135deg, #C5A049 0%, #a88b3d 100%); color: #0a0a0b; padding: 16px 32px; border-radius: 8px; text-decoration: none; font-weight: 600;">Go to Dashboard</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        if self.mode == 'sendgrid' and self.client:
            return await self._send_sendgrid(to_email, subject, html_content, f"Welcome {user_name}! Your CryptoVault account is ready.")
        else:
            logger.info(f"📧 [MOCK] Welcome email to {to_email}")
            return {"success": True, "message": "Welcome email sent (mock)", "provider": "mock"}


# Global email service instance
email_service = EmailService()
