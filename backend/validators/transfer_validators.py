"""
P2P Transfer Validation Schemas with Smart Gas Fee Support
Enterprise-grade validation for peer-to-peer transfers
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from decimal import Decimal


# Valid priority levels for fee calculation
VALID_PRIORITIES = ("low", "medium", "high", "urgent")

# Supported currencies
SUPPORTED_CURRENCIES = {
    # Cryptocurrencies
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "DOT", "LINK",
    "DOGE", "SHIB", "MATIC", "LTC", "UNI",
    # Stablecoins
    "USDT", "USDC", "DAI", "BUSD",
    # Fiat
    "USD", "EUR", "GBP",
}


class P2PTransferRequest(BaseModel):
    """Peer-to-peer transfer request with smart gas fee support"""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    currency: str = Field(
        default="USD",
        min_length=2, 
        max_length=10, 
        description="Currency code (BTC, ETH, USD, etc.)"
    )
    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    note: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Optional transfer note"
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        default="medium",
        description="Fee priority level (affects confirmation time and gas fee)"
    )
    two_fa_code: Optional[str] = Field(
        None, 
        min_length=6, 
        max_length=8, 
        description="2FA code if enabled"
    )
    
    @validator('currency')
    def validate_currency(cls, v):
        """Normalize and validate currency code"""
        v = v.strip().upper()
        if v not in SUPPORTED_CURRENCIES:
            raise ValueError(
                f'Unsupported currency: {v}. Supported: {", ".join(sorted(SUPPORTED_CURRENCIES))}'
            )
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount precision and minimum"""
        if v.as_tuple().exponent < -8:
            raise ValueError('Amount can have maximum 8 decimal places')
        if v < Decimal('0.00000001'):
            raise ValueError('Amount too small (minimum 0.00000001)')
        return v
    
    @validator('note')
    def validate_note(cls, v):
        """Sanitize note/message"""
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
        json_schema_extra = {
            "example": {
                "recipient_email": "recipient@example.com",
                "currency": "BTC",
                "amount": "0.001",
                "note": "Thanks for dinner!",
                "priority": "medium"
            }
        }


class FeeEstimateRequest(BaseModel):
    """Fee estimation request for transfer preview"""
    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    currency: str = Field(
        default="USD",
        min_length=2,
        max_length=10,
        description="Currency code"
    )
    
    @validator('currency')
    def validate_currency(cls, v):
        """Normalize currency code"""
        return v.strip().upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount": "0.01",
                "currency": "BTC"
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
