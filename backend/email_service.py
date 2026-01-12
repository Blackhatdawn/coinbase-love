"""
Email Service Module for CryptoVault
Supports multiple providers: Mock (dev), Resend, SendGrid, AWS SES, SMTP
Production-ready with async sending, templates, error handling, and config integration.
"""

import logging
import os  # Added for os.environ (provider keys – secure practice)
from typing import Optional, Tuple
from datetime import datetime
import uuid

import httpx  # For async HTTP (Resend/SendGrid)
import boto3  # For AWS SES (sync – fine for low volume)
from botocore.exceptions import ClientError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Unified email service with multiple providers.
    Configured via settings (pydantic) – provider keys from os.environ for security.
    Async where possible for performance.
    """

    def __init__(self):
        self.provider = settings.email_service.lower()
        self.from_email = settings.email_from
        self.from_name = settings.email_from_name
        self.app_url = settings.app_url

        # Provider-specific keys from os.environ (secure – not validated in settings)
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.resend_api_key = os.environ.get('RESEND_API_KEY')
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')

        logger.info(f"📧 Email service initialized: provider={self.provider}")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email using configured provider. Returns success status."""
        try:
            if self.provider == "resend":
                return await self._send_resend(to_email, subject, html_content, text_content)
            elif self.provider == "sendgrid":
                return await self._send_sendgrid(to_email, subject, html_content, text_content)
            elif self.provider == "ses":
                return self._send_ses(to_email, subject, html_content, text_content)
            elif self.provider == "smtp":
                return self._send_smtp(to_email, subject, html_content, text_content)
            else:
                # Mock for dev/local
                return self._send_mock(to_email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False

    def _send_mock(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Mock provider – logs email content (dev only)."""
        logger.info("=" * 80)
        logger.info("📧 MOCK EMAIL (Development Mode)")
        logger.info("=" * 80)
        logger.info(f"To: {to_email}")
        logger.info(f"From: {self.from_name} <{self.from_email}>")
        logger.info(f"Subject: {subject}")
        logger.info("-" * 80)
        logger.info(f"Text:\n{text_content or 'No text version'}")
        logger.info(f"HTML preview:\n{html_content[:500]}...")
        logger.info("=" * 80)
        return True

    async def _send_resend(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Send via Resend (recommended – async)."""
        if not self.resend_api_key:
            logger.error("❌ Resend API key missing")
            return False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": f"{self.from_name} <{self.from_email}>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                        "text": text_content or ""
                    },
                    timeout=10.0
                )

                if response.status_code in [200, 201]:
                    logger.info(f"✅ Email sent via Resend to {to_email} (ID: {response.json().get('id')})")
                    return True
                else:
                    logger.error(f"❌ Resend error {response.status_code}: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ Resend send failed: {str(e)}")
                return False

    async def _send_sendgrid(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Send via SendGrid (async via httpx)."""
        if not self.sendgrid_api_key:
            logger.error("❌ SendGrid API key missing")
            return False

        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": self.from_email, "name": self.from_name},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_content}]
                }
                if text_content:
                    payload["content"].insert(0, {"type": "text/plain", "value": text_content})

                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 202:
                    logger.info(f"✅ Email sent via SendGrid to {to_email}")
                    return True
                else:
                    logger.error(f"❌ SendGrid error {response.status_code}: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ SendGrid send failed: {str(e)}")
                return False

    def _send_ses(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Send via AWS SES (sync)."""
        try:
            client = boto3.client("ses", region_name=self.aws_region)

            body = {"Html": {"Charset": "UTF-8", "Data": html_content}}
            if text_content:
                body["Text"] = {"Charset": "UTF-8", "Data": text_content}

            response = client.send_email(
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Body": body,
                    "Subject": {"Charset": "UTF-8", "Data": subject},
                },
                Source=f"{self.from_name} <{self.from_email}>",
            )

            logger.info(f"✅ Email sent via SES to {to_email} (MessageId: {response['MessageId']})")
            return True

        except ClientError as e:
            logger.error(f"❌ AWS SES error: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"❌ SES send failed: {str(e)}")
            return False

    def _send_smtp(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Send via SMTP (sync)."""
        if not self.smtp_username or not self.smtp_password:
            logger.error("❌ SMTP credentials missing")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            if text_content:
                message.attach(MIMEText(text_content, "plain"))

            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            logger.info(f"✅ Email sent via SMTP to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ SMTP send failed: {str(e)}")
            return False

    # ============================================
    # EMAIL TEMPLATES (polished HTML)
    # ============================================

    def get_verification_email(self, name: str, code: str, token: str) -> Tuple[str, str, str]:
        """Verification email template."""
        subject = "Verify your CryptoVault account"

        verification_link = f"{self.app_url}/verify-email?token={token}"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f4f9; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
                .content {{ padding: 40px; }}
                .code {{ font-size: 36px; font-weight: bold; letter-spacing: 10px; background: #f0f0ff; padding: 20px; text-align: center; border-radius: 10px; margin: 30px 0; color: #667eea; }}
                .button {{ display: block; width: 200px; margin: 30px auto; background: #667eea; color: white; text-align: center; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                .footer {{ text-align: center; padding: 30px; color: #888; font-size: 12px; background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Verify Your Email</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    <p>Welcome to CryptoVault! Please verify your email to activate your account.</p>
                    <p><strong>Your verification code:</strong></p>
                    <div class="code">{code}</div>
                    <p>Or click the button below:</p>
                    <a href="{verification_link}" class="button">Verify Email</a>
                    <p style="color: #666; margin-top: 40px;">
                        This link expires in 24 hours. If you didn't sign up, ignore this email.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2026 CryptoVault. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Hi {name},

        Welcome to CryptoVault! Verify your email with this code: {code}

        Or use this link: {verification_link}

        Link expires in 24 hours. Ignore if not you.

        © 2026 CryptoVault
        """

        return subject, html_content, text_content

    def get_password_reset_email(self, name: str, reset_link: str) -> Tuple[str, str, str]:
        """Password reset template."""
        subject = "Reset your CryptoVault password"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f4f9; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
                .content {{ padding: 40px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 30px 0; }}
                .button {{ display: block; width: 200px; margin: 30px auto; background: #667eea; color: white; text-align: center; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                .footer {{ text-align: center; padding: 30px; color: #888; font-size: 12px; background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Password Reset</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    <p>We received a request to reset your CryptoVault password.</p>
                    <a href="{reset_link}" class="button">Reset Password</a>
                    <div class="warning">
                        <strong>Security Notice:</strong> This link expires in 1 hour. If you didn't request this, ignore it – your password remains safe.
                    </div>
                </div>
                <div class="footer">
                    <p>© 2026 CryptoVault. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Hi {name},

        Reset your CryptoVault password here: {reset_link}

        Link expires in 1 hour. Ignore if not requested.

        © 2026 CryptoVault
        """

        return subject, html_content, text_content

    def get_welcome_email(self, name: str) -> Tuple[str, str, str]:
        """Welcome email after verification."""
        subject = "Welcome to CryptoVault! 🎉"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to CryptoVault</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f4f9; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
                .content {{ padding: 40px; }}
                .feature {{ background: #f8f9ff; padding: 20px; margin: 20px 0; border-radius: 10px; border-left: 5px solid #667eea; }}
                .button {{ display: block; width: 200px; margin: 30px auto; background: #667eea; color: white; text-align: center; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                .footer {{ text-align: center; padding: 30px; color: #888; font-size: 12px; background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome aboard!</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    <p>Your CryptoVault account is ready! Start tracking and trading cryptocurrencies securely.</p>
                    <div class="feature">
                        <strong>📊 Live Prices</strong> – Real-time market data
                    </div>
                    <div class="feature">
                        <strong>💼 Portfolio Tracking</strong> – Manage your holdings
                    </div>
                    <div class="feature">
                        <strong>🔐 Maximum Security</strong> – 2FA, encryption, audit logs
                    </div>
                    <a href="{self.app_url}/dashboard" class="button">Open Dashboard</a>
                </div>
                <div class="footer">
                    <p>© 2026 CryptoVault. All rights reserved.</p>
                    <p>Questions? Reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Hi {name},

        Welcome to CryptoVault! Your account is ready.

        Features:
        - Live cryptocurrency prices
        - Portfolio tracking
        - Top-tier security

        Get started: {self.app_url}/dashboard

        © 2026 CryptoVault
        """

        return subject, html_content, text_content

# Global instance
email_service = EmailService()

# Token utilities (unchanged)
def generate_verification_code() -> str:
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))

def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)

def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(64)

def get_token_expiration(hours: int = 24) -> datetime:
    return datetime.utcnow() + timedelta(hours=hours)
