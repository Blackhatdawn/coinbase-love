"""
Price Alerts Validation Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from decimal import Decimal


class CreateAlertRequest(BaseModel):
    """Create a new price alert"""
    symbol: str = Field(..., min_length=2, max_length=10, description="Cryptocurrency symbol")
    condition: Literal["above", "below", "crosses_up", "crosses_down"] = Field(..., description="Alert condition")
    target_price: Decimal = Field(..., gt=0, description="Target price")
    notification_method: Literal["email", "push", "sms", "all"] = Field("email", description="Notification method")
    is_recurring: bool = Field(False, description="Recurring alert (reactivates after trigger)")
    notes: Optional[str] = Field(None, max_length=200, description="Optional notes")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Normalize symbol"""
        return v.strip().upper()
    
    @validator('target_price')
    def validate_target_price(cls, v):
        """Validate price precision"""
        if v.as_tuple().exponent < -8:
            raise ValueError('Price can have maximum 8 decimal places')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTC",
                "condition": "above",
                "target_price": "50000.00",
                "notification_method": "email",
                "is_recurring": False
            }
        }


class UpdateAlertRequest(BaseModel):
    """Update existing price alert"""
    target_price: Optional[Decimal] = Field(None, gt=0, description="New target price")
    notification_method: Optional[Literal["email", "push", "sms", "all"]] = Field(None, description="Notification method")
    is_active: Optional[bool] = Field(None, description="Active status")
    notes: Optional[str] = Field(None, max_length=200, description="Updated notes")
    
    @validator('target_price')
    def validate_target_price(cls, v):
        """Validate price precision"""
        if v and v.as_tuple().exponent < -8:
            raise ValueError('Price can have maximum 8 decimal places')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "target_price": "55000.00",
                "is_active": True
            }
        }


class DeleteAlertRequest(BaseModel):
    """Delete price alert"""
    alert_id: str = Field(..., description="Alert ID to delete")
    
    class Config:
        schema_extra = {
            "example": {
                "alert_id": "alert_123456789"
            }
        }
