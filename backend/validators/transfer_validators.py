"""
P2P Transfer Validation Schemas
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from decimal import Decimal


class P2PTransferRequest(BaseModel):
    """Peer-to-peer transfer request"""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    cryptocurrency: str = Field(..., min_length=2, max_length=10, description="Cryptocurrency symbol")
    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    message: Optional[str] = Field(None, max_length=200, description="Optional message")
    two_fa_code: Optional[str] = Field(None, min_length=6, max_length=8, description="2FA code if enabled")
    
    @validator('cryptocurrency')
    def validate_cryptocurrency(cls, v):
        """Normalize cryptocurrency symbol"""
        return v.strip().upper()
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount precision and minimum"""
        if v.as_tuple().exponent < -8:
            raise ValueError('Amount can have maximum 8 decimal places')
        if v < Decimal('0.00000001'):
            raise ValueError('Amount too small (minimum 0.00000001)')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        """Sanitize message"""
        if v:
            v = v.strip()
            # Remove multiple spaces
            v = ' '.join(v.split())
        return v
    
    @validator('two_fa_code')
    def validate_2fa_code(cls, v):
        """Validate 2FA code"""
        if v and not v.isdigit():
            raise ValueError('2FA code must be numeric')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "recipient@example.com",
                "cryptocurrency": "BTC",
                "amount": "0.001",
                "message": "Thanks for dinner!"
            }
        }


class AcceptTransferRequest(BaseModel):
    """Accept incoming P2P transfer"""
    transfer_id: str = Field(..., description="Transfer ID")
    
    class Config:
        schema_extra = {
            "example": {
                "transfer_id": "transfer_123456789"
            }
        }


class RejectTransferRequest(BaseModel):
    """Reject incoming P2P transfer"""
    transfer_id: str = Field(..., description="Transfer ID")
    reason: Optional[str] = Field(None, max_length=200, description="Rejection reason")
    
    @validator('reason')
    def validate_reason(cls, v):
        """Sanitize reason"""
        if v:
            v = v.strip()
            v = ' '.join(v.split())
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "transfer_id": "transfer_123456789",
                "reason": "Incorrect amount"
            }
        }
