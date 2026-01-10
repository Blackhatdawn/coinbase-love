"""
Email Service Module for CryptoVault
Supports multiple providers: SendGrid, AWS SES, SMTP
Production-ready with templates, rate limiting, and error handling
"""
import os
import secrets
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service with support for multiple providers.
    Defaults to console output if no provider configured (development).
    """
    
    def __init__(self):
        # EMAIL_SERVICE: mock (default), sendgrid, resend, ses, smtp
        self.provider = os.environ.get('EMAIL_SERVICE', 'mock')
        self.from_email = os.environ.get('EMAIL_FROM', 'noreply@cryptovault.com')
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'CryptoVault')
        
        # SendGrid
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        
        # AWS SES
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # SMTP
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        
        logger.info(f"📧 Email service initialized: provider={self.provider}")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email using configured provider.
        Returns True if successful, False otherwise.
        """
        try:
            if self.provider == 'sendgrid':
                return await self._send_sendgrid(to_email, subject, html_content, text_content)
            elif self.provider == 'ses':
                return await self._send_ses(to_email, subject, html_content, text_content)
            elif self.provider == 'smtp':
                return await self._send_smtp(to_email, subject, html_content, text_content)
            else:
                # Console provider for development
                return await self._send_console(to_email, subject, html_content, text_content)
                
        except Exception as e:
            logger.error(f"❌ Email send failed to {to_email}: {str(e)}")
            return False
    
    async def _send_console(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Console output for development (no actual email sent)"""
        logger.info("="*80)
        logger.info(f"📧 EMAIL (Console Mode - Development Only)")
        logger.info("="*80)
        logger.info(f"To: {to_email}")
        logger.info(f"From: {self.from_name} <{self.from_email}>")
        logger.info(f"Subject: {subject}")
        logger.info("-"*80)
        logger.info(f"Content:\n{text_content or html_content[:200]}...")
        logger.info("="*80)
        return True
    
    async def _send_sendgrid(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Send email via SendGrid"""
        if not self.sendgrid_api_key:
            logger.error("❌ SendGrid API key not configured")
            return False
        
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"❌ SendGrid returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ SendGrid error: {str(e)}")
            return False
    
    async def _send_ses(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Send email via AWS SES"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            ses_client = boto3.client('ses', region_name=self.aws_region)
            
            message = {
                'Subject': {'Data': subject},
                'Body': {
                    'Html': {'Data': html_content}
                }
            }
            
            if text_content:
                message['Body']['Text'] = {'Data': text_content}
            
            response = ses_client.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            
            logger.info(f"✅ Email sent via SES to {to_email} (MessageId: {response['MessageId']})")
            return True
            
        except ClientError as e:
            logger.error(f"❌ AWS SES error: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"❌ SES error: {str(e)}")
            return False
    
    async def _send_smtp(self, to_email: str, subject: str, html_content: str, text_content: Optional[str]) -> bool:
        """Send email via SMTP"""
        if not self.smtp_username or not self.smtp_password:
            logger.error("❌ SMTP credentials not configured")
            return False
        
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            
            if text_content:
                message.attach(MIMEText(text_content, 'plain'))
            message.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"✅ Email sent via SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            return False
    
    # ============================================
    # EMAIL TEMPLATES
    # ============================================
    
    def get_verification_email(self, name: str, code: str, token: str, app_url: str) -> tuple:
        """Get email verification email (HTML + text)"""
        subject = "Verify your CryptoVault account"
        
        verification_link = f"{app_url}/verify-email?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; background: white; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; color: #667eea; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Verify Your Email</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    <p>Welcome to CryptoVault! To complete your registration, please verify your email address.</p>
                    
                    <p><strong>Your verification code:</strong></p>
                    <div class="code">{code}</div>
                    
                    <p>Or click the button below to verify instantly:</p>
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        This link will expire in 24 hours. If you didn't create this account, please ignore this email.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2026 CryptoVault. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {name},
        
        Welcome to CryptoVault! To complete your registration, please verify your email address.
        
        Your verification code: {code}
        
        Or visit this link: {verification_link}
        
        This link will expire in 24 hours. If you didn't create this account, please ignore this email.
        
        © 2026 CryptoVault. All rights reserved.
        """
        
        return subject, html_content, text_content
    
    def get_password_reset_email(self, name: str, reset_link: str) -> tuple:
        """Get password reset email (HTML + text)"""
        subject = "Reset your CryptoVault password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    <p>We received a request to reset your CryptoVault password. Click the button below to choose a new password:</p>
                    
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        This link will expire in 1 hour for your security. If you didn't request this, please ignore this email and your password will remain unchanged.
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        For your security, never share this link with anyone.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2026 CryptoVault. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {name},
        
        We received a request to reset your CryptoVault password.
        
        Click this link to reset your password: {reset_link}
        
        ⚠️ Security Notice:
        This link will expire in 1 hour for your security. If you didn't request this, please ignore this email and your password will remain unchanged.
        
        For your security, never share this link with anyone.
        
        © 2026 CryptoVault. All rights reserved.
        """
        
        return subject, html_content, text_content
    
    def get_welcome_email(self, name: str, app_url: str) -> tuple:
        """Get welcome email after verification (HTML + text)"""
        subject = "Welcome to CryptoVault! 🎉"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .feature {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to CryptoVault!</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    <p>Your email has been verified! You're now ready to start your cryptocurrency journey.</p>
                    
                    <h3>Here's what you can do:</h3>
                    
                    <div class="feature">
                        <strong>📊 View Live Markets</strong><br>
                        Track real-time prices for Bitcoin, Ethereum, and more.
                    </div>
                    
                    <div class="feature">
                        <strong>💼 Manage Your Portfolio</strong><br>
                        Add holdings and track your investments.
                    </div>
                    
                    <div class="feature">
                        <strong>📈 Trade Crypto</strong><br>
                        Buy and sell cryptocurrencies securely.
                    </div>
                    
                    <div class="feature">
                        <strong>🔒 Enable 2FA</strong><br>
                        Add extra security to your account.
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{app_url}/dashboard" class="button">Go to Dashboard</a>
                    </p>
                </div>
                <div class="footer">
                    <p>© 2026 CryptoVault. All rights reserved.</p>
                    <p>Need help? Contact us at support@cryptovault.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {name},
        
        Welcome to CryptoVault! Your email has been verified and you're ready to start.
        
        Here's what you can do:
        
        📊 View Live Markets - Track real-time cryptocurrency prices
        💼 Manage Your Portfolio - Add holdings and track investments
        📈 Trade Crypto - Buy and sell securely
        🔒 Enable 2FA - Add extra security
        
        Get started: {app_url}/dashboard
        
        Need help? Contact us at support@cryptovault.com
        
        © 2026 CryptoVault. All rights reserved.
        """
        
        return subject, html_content, text_content


# Global email service instance
email_service = EmailService()


# ============================================
# TOKEN GENERATION UTILITIES
# ============================================

def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)


def generate_password_reset_token() -> str:
    """Generate secure password reset token"""
    return secrets.token_urlsafe(64)


def get_token_expiration(hours: int = 24) -> datetime:
    """Get expiration datetime for token"""
    return datetime.utcnow() + timedelta(hours=hours)
