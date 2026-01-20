"""
CryptoVault Email Templates
Professional, branded HTML email templates for all transactional emails
"""

from typing import Optional

from config import settings

# Base URL for email assets (configurable via backend .env)
SITE_URL = settings.app_url.rstrip("/")
LOGO_URL = settings.public_logo_url or f"{SITE_URL}/favicon.svg"
SUPPORT_EMAIL = settings.public_support_email or "support@cryptovault.financial"

def get_base_template(content: str, preheader: str = "") -> str:
    """
    Base email template with CryptoVault branding
    All templates extend this base
    """
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>CryptoVault</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;">
    <!-- Preheader text (hidden) -->
    <div style="display: none; max-height: 0; overflow: hidden; font-size: 1px; line-height: 1px; color: #0a0a0a;">
        {preheader}
    </div>
    
    <!-- Email Container -->
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #0a0a0a;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                
                <!-- Main Content Card -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width: 600px; background-color: #141414; border-radius: 16px; border: 1px solid rgba(251, 191, 36, 0.1);">
                    
                    <!-- Header with Logo -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 30px;">
                            <a href="{SITE_URL}" style="text-decoration: none;">
                                <img src="{LOGO_URL}" alt="CryptoVault" width="60" height="60" style="display: block;">
                            </a>
                            <h1 style="margin: 16px 0 0; font-size: 24px; font-weight: 700; color: #ffffff;">
                                Crypto<span style="color: #FBBF24;">Vault</span>
                            </h1>
                            <p style="margin: 4px 0 0; font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px;">
                                Secure Global Trading
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 0 40px 40px;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid rgba(251, 191, 36, 0.1);">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="margin: 0 0 16px; font-size: 12px; color: #6b7280;">
                                            Follow us on social media
                                        </p>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="padding: 0 8px;">
                                                    <a href="https://twitter.com/CryptoVaultFin" style="color: #FBBF24; text-decoration: none;">Twitter</a>
                                                </td>
                                                <td style="padding: 0 8px; color: #374151;">|</td>
                                                <td style="padding: 0 8px;">
                                                    <a href="https://linkedin.com/company/cryptovault-financial" style="color: #FBBF24; text-decoration: none;">LinkedIn</a>
                                                </td>
                                                <td style="padding: 0 8px; color: #374151;">|</td>
                                                <td style="padding: 0 8px;">
                                                    <a href="https://discord.gg/cryptovault" style="color: #FBBF24; text-decoration: none;">Discord</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Legal Footer -->
                    <tr>
                        <td style="padding: 20px 40px 30px; background-color: #0a0a0a; border-radius: 0 0 16px 16px;">
                            <p style="margin: 0 0 8px; font-size: 11px; color: #4b5563; text-align: center;">
                                © 2025 CryptoVault Financial, Inc. All rights reserved.
                            </p>
                            <p style="margin: 0 0 8px; font-size: 11px; color: #4b5563; text-align: center;">
                                1201 Market Street, Suite 101, Wilmington, DE 19801
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #4b5563; text-align: center;">
                                <a href="{SITE_URL}/privacy" style="color: #FBBF24; text-decoration: none;">Privacy</a> · 
                                <a href="{SITE_URL}/terms" style="color: #FBBF24; text-decoration: none;">Terms</a> · 
                                <a href="{SITE_URL}/help" style="color: #FBBF24; text-decoration: none;">Help Center</a>
                            </p>
                        </td>
                    </tr>
                    
                </table>
                
            </td>
        </tr>
    </table>
</body>
</html>'''


def welcome_email(name: str) -> str:
    """Welcome/Onboarding email for new users"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            Welcome to CryptoVault, {name}! 🎉
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Thank you for joining the most secure cryptocurrency platform. Your journey into digital assets starts here.
        </p>
        
        <!-- Getting Started Steps -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 20px; background-color: #1f1f1f; border-radius: 12px; margin-bottom: 16px;">
                    <h3 style="margin: 0 0 16px; font-size: 16px; font-weight: 600; color: #FBBF24;">
                        Get Started in 3 Steps:
                    </h3>
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="width: 32px; height: 32px; background-color: #FBBF24; border-radius: 50%; text-align: center; vertical-align: middle; font-weight: 700; color: #0a0a0a;">1</td>
                                        <td style="padding-left: 16px;">
                                            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #ffffff;">Verify Your Identity</p>
                                            <p style="margin: 4px 0 0; font-size: 13px; color: #6b7280;">Complete KYC to unlock full trading features</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="width: 32px; height: 32px; background-color: #FBBF24; border-radius: 50%; text-align: center; vertical-align: middle; font-weight: 700; color: #0a0a0a;">2</td>
                                        <td style="padding-left: 16px;">
                                            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #ffffff;">Enable 2FA Security</p>
                                            <p style="margin: 4px 0 0; font-size: 13px; color: #6b7280;">Protect your account with two-factor authentication</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="width: 32px; height: 32px; background-color: #FBBF24; border-radius: 50%; text-align: center; vertical-align: middle; font-weight: 700; color: #0a0a0a;">3</td>
                                        <td style="padding-left: 16px;">
                                            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #ffffff;">Make Your First Deposit</p>
                                            <p style="margin: 4px 0 0; font-size: 13px; color: #6b7280;">Fund your account and start trading</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 16px;">
                    <a href="{SITE_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        Go to Dashboard
                    </a>
                </td>
            </tr>
        </table>
        
        <p style="margin: 0; font-size: 13px; color: #6b7280; text-align: center;">
            Questions? Our support team is here 24/7 at <a href="mailto:{SUPPORT_EMAIL}" style="color: #FBBF24;">{SUPPORT_EMAIL}</a>
        </p>
    '''
    return get_base_template(content, f"Welcome to CryptoVault, {name}! Start your crypto journey today.")


def email_verification(name: str, otp_code: str) -> str:
    """Email verification with OTP code"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            Verify Your Email
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, please use the verification code below to complete your email verification. This code expires in 10 minutes.
        </p>
        
        <!-- OTP Code Box -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 24px; background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 12px;">
                    <p style="margin: 0 0 8px; font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 2px;">
                        Your Verification Code
                    </p>
                    <p style="margin: 0; font-size: 40px; font-weight: 700; color: #FBBF24; letter-spacing: 8px; font-family: monospace;">
                        {otp_code}
                    </p>
                </td>
            </tr>
        </table>
        
        <p style="margin: 24px 0 0; font-size: 13px; color: #6b7280; text-align: center;">
            If you didn't request this code, please ignore this email or contact support if you have concerns.
        </p>
        
        <!-- Security Notice -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 24px;">
            <tr>
                <td style="padding: 16px; background-color: #1f1f1f; border-radius: 8px; border-left: 3px solid #FBBF24;">
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                        🔒 <strong style="color: #ffffff;">Security Tip:</strong> CryptoVault will never ask for your password or private keys via email.
                    </p>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"Your CryptoVault verification code: {otp_code}")


def password_reset(name: str, reset_link: str) -> str:
    """Password reset email"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            Reset Your Password
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, we received a request to reset your password. Click the button below to create a new password. This link expires in 1 hour.
        </p>
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 8px 0 24px;">
                    <a href="{reset_link}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        Reset Password
                    </a>
                </td>
            </tr>
        </table>
        
        <p style="margin: 0 0 16px; font-size: 13px; color: #6b7280;">
            Or copy and paste this link into your browser:
        </p>
        <p style="margin: 0 0 24px; font-size: 12px; color: #FBBF24; word-break: break-all;">
            {reset_link}
        </p>
        
        <!-- Security Notice -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 16px; background-color: #1f1f1f; border-radius: 8px; border-left: 3px solid #EF4444;">
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                        ⚠️ <strong style="color: #ffffff;">Didn't request this?</strong> If you didn't request a password reset, please secure your account immediately by changing your password and enabling 2FA.
                    </p>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, "Reset your CryptoVault password")


def deposit_confirmation(name: str, amount: str, asset: str, tx_hash: str) -> str:
    """Deposit confirmation email"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            Deposit Confirmed ✓
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, your deposit has been successfully credited to your CryptoVault account.
        </p>
        
        <!-- Transaction Details -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 24px; background-color: #1f1f1f; border-radius: 12px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Amount</p>
                                <p style="margin: 4px 0 0; font-size: 24px; font-weight: 700; color: #10B981;">
                                    +{amount} {asset}
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Asset</p>
                                <p style="margin: 4px 0 0; font-size: 16px; color: #ffffff;">{asset}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Transaction Hash</p>
                                <p style="margin: 4px 0 0; font-size: 12px; color: #FBBF24; word-break: break-all; font-family: monospace;">
                                    {tx_hash}
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        View Balance
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"Your {amount} {asset} deposit has been confirmed")


def withdrawal_confirmation(name: str, amount: str, asset: str, address: str, tx_hash: str) -> str:
    """Withdrawal confirmation email"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            Withdrawal Processed
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, your withdrawal request has been processed and sent to the blockchain.
        </p>
        
        <!-- Transaction Details -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 24px; background-color: #1f1f1f; border-radius: 12px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Amount</p>
                                <p style="margin: 4px 0 0; font-size: 24px; font-weight: 700; color: #EF4444;">
                                    -{amount} {asset}
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Destination Address</p>
                                <p style="margin: 4px 0 0; font-size: 12px; color: #ffffff; word-break: break-all; font-family: monospace;">
                                    {address}
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Transaction Hash</p>
                                <p style="margin: 4px 0 0; font-size: 12px; color: #FBBF24; word-break: break-all; font-family: monospace;">
                                    {tx_hash}
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- Security Notice -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 24px;">
            <tr>
                <td style="padding: 16px; background-color: #1f1f1f; border-radius: 8px; border-left: 3px solid #EF4444;">
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                        ⚠️ <strong style="color: #ffffff;">Didn't authorize this?</strong> If you didn't initiate this withdrawal, please contact support immediately and freeze your account.
                    </p>
                </td>
            </tr>
        </table>
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/transactions" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        View Transaction History
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"Your withdrawal of {amount} {asset} has been processed")


def two_factor_reminder(name: str) -> str:
    """2FA setup reminder email"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            Secure Your Account with 2FA
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, we noticed you haven't enabled Two-Factor Authentication (2FA) yet. Adding 2FA significantly increases the security of your account.
        </p>
        
        <!-- Benefits -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 20px; background-color: #1f1f1f; border-radius: 12px;">
                    <h3 style="margin: 0 0 16px; font-size: 16px; font-weight: 600; color: #FBBF24;">
                        Why enable 2FA?
                    </h3>
                    <ul style="margin: 0; padding: 0 0 0 20px; color: #9ca3af; font-size: 14px; line-height: 1.8;">
                        <li>Protect against unauthorized access even if your password is compromised</li>
                        <li>Required for higher withdrawal limits</li>
                        <li>Industry best practice for cryptocurrency security</li>
                        <li>Takes less than 2 minutes to set up</li>
                    </ul>
                </td>
            </tr>
        </table>
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/dashboard?setup=2fa" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        Enable 2FA Now
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, "Protect your CryptoVault account - Enable 2FA")


def security_alert(name: str, alert_type: str, details: str, ip_address: str, location: str) -> str:
    """Security alert email (login, password change, etc.)"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            🔐 Security Alert
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, we detected {alert_type} on your CryptoVault account.
        </p>
        
        <!-- Alert Details -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 24px; background-color: #1f1f1f; border-radius: 12px; border-left: 3px solid #FBBF24;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 8px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Activity</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff;">{details}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">IP Address</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff; font-family: monospace;">{ip_address}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Location</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff;">{location}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- Warning -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 24px;">
            <tr>
                <td style="padding: 16px; background-color: rgba(239, 68, 68, 0.1); border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.2);">
                    <p style="margin: 0; font-size: 14px; color: #EF4444; font-weight: 600;">
                        Was this you?
                    </p>
                    <p style="margin: 8px 0 0; font-size: 13px; color: #9ca3af;">
                        If you don't recognize this activity, please secure your account immediately by changing your password and contacting support.
                    </p>
                </td>
            </tr>
        </table>
        
        <!-- CTA Buttons -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/dashboard?security=true" style="display: inline-block; padding: 14px 24px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 8px; margin-right: 12px;">
                        Review Activity
                    </a>
                    <a href="{SITE_URL}/help" style="display: inline-block; padding: 14px 24px; background-color: #1f1f1f; border: 1px solid #374151; color: #ffffff; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        Contact Support
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"Security Alert: {alert_type} detected on your account")


def kyc_status_update(name: str, status: str, level: int, message: Optional[str] = None) -> str:
    """KYC status update email"""
    status_colors = {
        "approved": "#10B981",
        "rejected": "#EF4444",
        "pending": "#FBBF24",
    }
    status_icons = {
        "approved": "✓",
        "rejected": "✗",
        "pending": "⏳",
    }
    
    color = status_colors.get(status.lower(), "#FBBF24")
    icon = status_icons.get(status.lower(), "•")
    
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            KYC Verification Update
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, there's an update on your identity verification (Level {level}).
        </p>
        
        <!-- Status Badge -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 24px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                        <tr>
                            <td style="padding: 16px 32px; background-color: {color}20; border: 2px solid {color}; border-radius: 12px;">
                                <p style="margin: 0; font-size: 32px; text-align: center;">{icon}</p>
                                <p style="margin: 8px 0 0; font-size: 18px; font-weight: 700; color: {color}; text-transform: uppercase;">
                                    {status}
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        {f'<p style="margin: 0 0 24px; font-size: 14px; color: #9ca3af; text-align: center; padding: 16px; background-color: #1f1f1f; border-radius: 8px;">{message}</p>' if message else ''}
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 16px 0 0;">
                    <a href="{SITE_URL}/dashboard?kyc=true" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        View KYC Status
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"KYC Verification {status.title()} - Level {level}")


def p2p_transfer_sent(
    sender_name: str,
    recipient_name: str,
    recipient_email: str,
    amount: str,
    asset: str,
    gas_fee: str,
    transaction_id: str,
    note: Optional[str] = None
) -> str:
    """P2P transfer sent confirmation email"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            Transfer Sent Successfully ✓
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {sender_name}, your transfer to {recipient_name} has been completed.
        </p>
        
        <!-- Transaction Details -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 24px; background-color: #1f1f1f; border-radius: 12px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Amount Sent</p>
                                <p style="margin: 4px 0 0; font-size: 24px; font-weight: 700; color: #EF4444;">
                                    -{amount} {asset}
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Network Fee</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #9ca3af;">
                                    {gas_fee}
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Recipient</p>
                                <p style="margin: 4px 0 0; font-size: 16px; color: #ffffff;">{recipient_name}</p>
                                <p style="margin: 2px 0 0; font-size: 12px; color: #6b7280;">{recipient_email}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Transaction ID</p>
                                <p style="margin: 4px 0 0; font-size: 12px; color: #FBBF24; word-break: break-all; font-family: monospace;">
                                    {transaction_id}
                                </p>
                            </td>
                        </tr>
                        {f'<tr><td style="padding: 12px 0; border-top: 1px solid #374151;"><p style="margin: 0; font-size: 12px; color: #6b7280;">Note</p><p style="margin: 4px 0 0; font-size: 14px; color: #ffffff; font-style: italic;">"{note}"</p></td></tr>' if note else ''}
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/transactions" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        View Transaction History
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"You sent {amount} {asset} to {recipient_name}")


def p2p_transfer_received(
    recipient_name: str,
    sender_name: str,
    sender_email: str,
    amount: str,
    asset: str,
    transaction_id: str,
    note: Optional[str] = None
) -> str:
    """P2P transfer received notification email"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            You Received {asset}! 🎉
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {recipient_name}, you just received a transfer from {sender_name}.
        </p>
        
        <!-- Transaction Details -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 24px; background-color: #1f1f1f; border-radius: 12px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Amount Received</p>
                                <p style="margin: 4px 0 0; font-size: 28px; font-weight: 700; color: #10B981;">
                                    +{amount} {asset}
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">From</p>
                                <p style="margin: 4px 0 0; font-size: 16px; color: #ffffff;">{sender_name}</p>
                                <p style="margin: 2px 0 0; font-size: 12px; color: #6b7280;">{sender_email}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Transaction ID</p>
                                <p style="margin: 4px 0 0; font-size: 12px; color: #FBBF24; word-break: break-all; font-family: monospace;">
                                    {transaction_id}
                                </p>
                            </td>
                        </tr>
                        {f'<tr><td style="padding: 12px 0; border-top: 1px solid #374151;"><p style="margin: 0; font-size: 12px; color: #6b7280;">Note from sender</p><p style="margin: 4px 0 0; font-size: 14px; color: #ffffff; font-style: italic;">"{note}"</p></td></tr>' if note else ''}
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 15px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        View Your Balance
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"You received {amount} {asset} from {sender_name}")


def price_alert_triggered(
    name: str,
    asset: str,
    current_price: str,
    target_price: str,
    condition: str,
    alert_id: str
) -> str:
    """Price alert triggered notification email"""
    condition_text = "reached" if condition == "above" else "dropped below"
    arrow = "↑" if condition == "above" else "↓"
    color = "#10B981" if condition == "above" else "#EF4444"
    
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            🔔 Price Alert Triggered
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, {asset} has {condition_text} your target price.
        </p>
        
        <!-- Price Details -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 24px; background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 12px;">
                    <p style="margin: 0 0 8px; font-size: 14px; color: #6b7280;">{asset}</p>
                    <p style="margin: 0; font-size: 36px; font-weight: 700; color: {color};">
                        {arrow} {current_price}
                    </p>
                    <p style="margin: 8px 0 0; font-size: 14px; color: #9ca3af;">
                        Target: {target_price}
                    </p>
                </td>
            </tr>
        </table>
        
        <!-- CTA Buttons -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/trade?asset={asset.lower()}" style="display: inline-block; padding: 14px 24px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 8px; margin-right: 12px;">
                        Trade Now
                    </a>
                    <a href="{SITE_URL}/alerts" style="display: inline-block; padding: 14px 24px; background-color: #1f1f1f; border: 1px solid #374151; color: #ffffff; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        Manage Alerts
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"Price Alert: {asset} {condition_text} {target_price}")


def login_new_device(
    name: str,
    device: str,
    browser: str,
    ip_address: str,
    location: str,
    login_time: str
) -> str:
    """New device login notification email"""
    content = f'''
        <h2 style="margin: 0 0 16px; font-size: 22px; font-weight: 600; color: #ffffff;">
            New Login Detected
        </h2>
        <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.6; color: #9ca3af;">
            Hi {name}, we detected a new login to your CryptoVault account.
        </p>
        
        <!-- Login Details -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 24px; background-color: #1f1f1f; border-radius: 12px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Device</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff;">{device}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Browser</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff;">{browser}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">IP Address</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff; font-family: monospace;">{ip_address}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #374151;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Location</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff;">{location}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">
                                <p style="margin: 0; font-size: 12px; color: #6b7280;">Time</p>
                                <p style="margin: 4px 0 0; font-size: 14px; color: #ffffff;">{login_time}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- Security Warning -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 24px;">
            <tr>
                <td style="padding: 16px; background-color: rgba(239, 68, 68, 0.1); border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.2);">
                    <p style="margin: 0; font-size: 14px; color: #EF4444; font-weight: 600;">
                        Was this you?
                    </p>
                    <p style="margin: 8px 0 0; font-size: 13px; color: #9ca3af;">
                        If you don't recognize this login, please secure your account immediately by changing your password and enabling 2FA.
                    </p>
                </td>
            </tr>
        </table>
        
        <!-- CTA Buttons -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 32px 0 0;">
                    <a href="{SITE_URL}/dashboard?security=true" style="display: inline-block; padding: 14px 24px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: #0a0a0a; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 8px; margin-right: 12px;">
                        Secure Account
                    </a>
                    <a href="{SITE_URL}/help" style="display: inline-block; padding: 14px 24px; background-color: #1f1f1f; border: 1px solid #374151; color: #ffffff; font-size: 14px; font-weight: 600; text-decoration: none; border-radius: 8px;">
                        Report Suspicious Activity
                    </a>
                </td>
            </tr>
        </table>
    '''
    return get_base_template(content, f"New login to your CryptoVault account from {location}")
