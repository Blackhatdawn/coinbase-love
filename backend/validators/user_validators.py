"""
User Management Validation Schemas
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re


class UserProfileUpdate(BaseModel):
    """Update user profile information"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar image URL")
    
    @validator('name')
    def validate_name(cls, v):
        """Sanitize and validate name"""
        if v:
            v = v.strip()
            v = ' '.join(v.split())
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v:
            # Remove common formatting characters
            v = re.sub(r'[\s\-\(\)\+]', '', v)
            if not v.isdigit() or len(v) < 10 or len(v) > 15:
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        """Validate avatar URL"""
        if v:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('Avatar URL must start with http:// or https://')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "phone": "+1234567890",
                "bio": "Crypto enthusiast and trader"
            }
        }


class UserPreferencesUpdate(BaseModel):
    """Update user preferences and settings"""
    language: Optional[str] = Field(None, regex="^(en|es|fr|de|zh|ja)$", description="Preferred language")
    currency: Optional[str] = Field(None, regex="^(USD|EUR|GBP|JPY|CNY)$", description="Preferred currency")
    timezone: Optional[str] = Field(None, max_length=50, description="User timezone")
    email_notifications: Optional[bool] = Field(None, description="Enable email notifications")
    push_notifications: Optional[bool] = Field(None, description="Enable push notifications")
    price_alerts: Optional[bool] = Field(None, description="Enable price alerts")
    newsletter: Optional[bool] = Field(None, description="Subscribe to newsletter")
    
    class Config:
        schema_extra = {
            "example": {
                "language": "en",
                "currency": "USD",
                "timezone": "America/New_York",
                "email_notifications": True,
                "price_alerts": True
            }
        }


class UserSecurityUpdate(BaseModel):
    """Update security settings"""
    enable_2fa: Optional[bool] = Field(None, description="Enable two-factor authentication")
    enable_withdrawal_whitelist: Optional[bool] = Field(None, description="Enable withdrawal whitelist")
    enable_login_alerts: Optional[bool] = Field(None, description="Enable login alerts")
    session_timeout: Optional[int] = Field(None, ge=5, le=1440, description="Session timeout in minutes")
    
    class Config:
        schema_extra = {
            "example": {
                "enable_2fa": True,
                "enable_withdrawal_whitelist": True,
                "session_timeout": 30
            }
        }
