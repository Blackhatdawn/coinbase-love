"""
Portfolio Management Validation Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal


class AddHoldingRequest(BaseModel):
    """Add a new asset to portfolio"""
    symbol: str = Field(..., min_length=2, max_length=10, description="Asset symbol")
    amount: Decimal = Field(..., gt=0, description="Amount of asset")
    purchase_price: Optional[Decimal] = Field(None, gt=0, description="Purchase price per unit")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate and normalize symbol"""
        v = v.strip().upper()
        if not v.isalnum():
            raise ValueError('Symbol must be alphanumeric')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount precision"""
        if v.as_tuple().exponent < -8:
            raise ValueError('Amount can have maximum 8 decimal places')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC",
                "amount": "0.5",
                "purchase_price": "45000.00",
                "notes": "Long-term hold"
            }
        }


class UpdateHoldingRequest(BaseModel):
    """Update existing portfolio holding"""
    amount: Optional[Decimal] = Field(None, gt=0, description="New amount")
    purchase_price: Optional[Decimal] = Field(None, gt=0, description="New purchase price")
    notes: Optional[str] = Field(None, max_length=500, description="Updated notes")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount precision"""
        if v and v.as_tuple().exponent < -8:
            raise ValueError('Amount can have maximum 8 decimal places')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "amount": "1.0",
                "purchase_price": "50000.00"
            }
        }


class RemoveHoldingRequest(BaseModel):
    """Remove asset from portfolio"""
    symbol: str = Field(..., min_length=2, max_length=10, description="Asset symbol")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate and normalize symbol"""
        return v.strip().upper()
