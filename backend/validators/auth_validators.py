"""
Authentication & Security Validation Schemas
Enterprise-grade input validation for auth endpoints
"""

from pydantic import BaseModel, EmailStr, Field, validator, constr
from typing import Optional
import re

# Password validation regex
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$"


class SignupRequest(BaseModel):
    """User registration request with strict validation"""
    email: EmailStr = Field(..., description="Valid email address")
    password: constr(min_length=8, max_length=128) = Field(..., description="Strong password")
    name: constr(min_length=2, max_length=100) = Field(..., description="Full name")
    referral_code: Optional[str] = Field(None, max_length=20, description="Optional referral code")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Enforce strong password policy"""
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                'Password must contain at least: '
                '1 uppercase letter, 1 lowercase letter, 1 digit, '
                '1 special character (@$!%*?&), and be 8-128 characters long'
            )
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Sanitize and validate name"""
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty or whitespace')
        # Remove multiple spaces
        v = ' '.join(v.split())
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v
    
    @validator('referral_code')
    def validate_referral_code(cls, v):
        """Validate referral code format"""
        if v:
            v = v.strip().upper()
            if not re.match(r'^[A-Z0-9]{4,20}$', v):
                raise ValueError('Invalid referral code format')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "name": "John Doe",
                "referral_code": "CRYPTO2024"
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=1, max_length=128, description="Password")
    remember_me: bool = Field(default=False, description="Extended session duration")
    device_name: Optional[str] = Field(None, max_length=100, description="Device identifier")
    
    @validator('device_name')
    def sanitize_device_name(cls, v):
        """Sanitize device name"""
        if v:
            v = v.strip()
            # Remove special characters except spaces and hyphens
            v = re.sub(r'[^a-zA-Z0-9\s\-]', '', v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        }


class EmailVerificationRequest(BaseModel):
    """Email verification with token or code"""
    email: EmailStr = Field(..., description="Email to verify")
    token: Optional[str] = Field(None, min_length=6, max_length=256, description="Verification token")
    code: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit verification code")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate verification code format"""
        if v and not v.isdigit():
            raise ValueError('Verification code must be 6 digits')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="Registered email address")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Password reset with token"""
    token: str = Field(..., min_length=32, max_length=256, description="Password reset token")
    new_password: constr(min_length=8, max_length=128) = Field(..., description="New strong password")
    confirm_password: constr(min_length=8, max_length=128) = Field(..., description="Password confirmation")
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Enforce strong password policy"""
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                'Password must contain at least: '
                '1 uppercase letter, 1 lowercase letter, 1 digit, '
                '1 special character (@$!%*?&), and be 8-128 characters long'
            )
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "a1b2c3d4e5f6...",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password for authenticated user"""
    current_password: str = Field(..., min_length=1, max_length=128, description="Current password")
    new_password: constr(min_length=8, max_length=128) = Field(..., description="New strong password")
    confirm_password: constr(min_length=8, max_length=128) = Field(..., description="Password confirmation")
    
    @validator('new_password')
    def validate_new_password_strength(cls, v, values):
        """Enforce strong password policy and prevent reuse"""
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                'Password must contain at least: '
                '1 uppercase letter, 1 lowercase letter, 1 digit, '
                '1 special character (@$!%*?&), and be 8-128 characters long'
            )
        # Prevent using current password as new password
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class TwoFactorSetupRequest(BaseModel):
    """2FA setup initiation"""
    method: str = Field(..., regex="^(totp|sms|email)$", description="2FA method")
    
    class Config:
        schema_extra = {
            "example": {
                "method": "totp"
            }
        }


class TwoFactorVerifyRequest(BaseModel):
    """2FA verification"""
    code: str = Field(..., min_length=6, max_length=8, description="2FA code")
    method: str = Field(..., regex="^(totp|sms|email)$", description="2FA method")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate 2FA code format"""
        if not v.isdigit():
            raise ValueError('2FA code must be numeric')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "code": "123456",
                "method": "totp"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: Optional[str] = Field(None, description="Refresh token (if not in cookie)")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
