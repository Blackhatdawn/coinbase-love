"""
Wallet Operations Validation Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal


class DepositRequest(BaseModel):
    """Request crypto deposit"""
    cryptocurrency: str = Field(..., min_length=2, max_length=10, description="Cryptocurrency symbol")
    network: Optional[str] = Field(None, max_length=20, description="Blockchain network")
    
    @validator('cryptocurrency')
    def validate_cryptocurrency(cls, v):
        """Normalize cryptocurrency symbol"""
        return v.strip().upper()
    
    @validator('network')
    def validate_network(cls, v):
        """Normalize network"""
        if v:
            return v.strip().upper()
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "cryptocurrency": "BTC",
                "network": "BITCOIN"
            }
        }


class WithdrawRequest(BaseModel):
    """Request crypto withdrawal"""
    cryptocurrency: str = Field(..., min_length=2, max_length=10, description="Cryptocurrency symbol")
    amount: Decimal = Field(..., gt=0, description="Withdrawal amount")
    address: str = Field(..., min_length=26, max_length=100, description="Withdrawal address")
    network: Optional[str] = Field(None, max_length=20, description="Blockchain network")
    memo: Optional[str] = Field(None, max_length=100, description="Memo/Tag (for certain currencies)")
    two_fa_code: Optional[str] = Field(None, min_length=6, max_length=8, description="2FA code if enabled")
    
    @validator('cryptocurrency')
    def validate_cryptocurrency(cls, v):
        """Normalize cryptocurrency symbol"""
        return v.strip().upper()
    
    @validator('amount')
    def validate_amount_precision(cls, v):
        """Validate amount precision"""
        if v.as_tuple().exponent < -8:
            raise ValueError('Amount can have maximum 8 decimal places')
        if v < Decimal('0.00000001'):
            raise ValueError('Amount too small (minimum 0.00000001)')
        return v
    
    @validator('address')
    def validate_address_format(cls, v):
        """Validate address format"""
        v = v.strip()
        if not v:
            raise ValueError('Address cannot be empty')
        # Basic validation - alphanumeric
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError('Invalid address format')
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
                "cryptocurrency": "BTC",
                "amount": "0.5",
                "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                "network": "BITCOIN"
            }
        }


class InternalTransferRequest(BaseModel):
    """Internal transfer between accounts"""
    from_account: str = Field(..., description="Source account type")
    to_account: str = Field(..., description="Destination account type")
    cryptocurrency: str = Field(..., min_length=2, max_length=10, description="Cryptocurrency symbol")
    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    
    @validator('cryptocurrency')
    def validate_cryptocurrency(cls, v):
        """Normalize cryptocurrency symbol"""
        return v.strip().upper()
    
    @validator('from_account', 'to_account')
    def validate_accounts_different(cls, v, values):
        """Ensure accounts are different"""
        if 'from_account' in values and v == values['from_account']:
            raise ValueError('Source and destination accounts must be different')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "from_account": "spot",
                "to_account": "futures",
                "cryptocurrency": "USDT",
                "amount": "1000.00"
            }
        }
