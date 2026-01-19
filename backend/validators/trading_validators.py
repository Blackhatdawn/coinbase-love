"""
Trading Validation Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime


class PlaceOrderRequest(BaseModel):
    """Place a new trading order"""
    trading_pair: str = Field(..., regex="^[A-Z]{2,10}/[A-Z]{2,10}$", description="Trading pair (e.g., BTC/USD)")
    order_type: Literal["market", "limit", "stop_loss", "stop_limit"] = Field(..., description="Order type")
    side: Literal["buy", "sell"] = Field(..., description="Order side")
    amount: Decimal = Field(..., gt=0, description="Order amount")
    price: Optional[Decimal] = Field(None, gt=0, description="Limit price (required for limit orders)")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="Stop price (required for stop orders)")
    time_in_force: Optional[Literal["GTC", "IOC", "FOK"]] = Field("GTC", description="Time in force")
    
    @validator('trading_pair')
    def validate_trading_pair(cls, v):
        """Normalize trading pair"""
        return v.upper()
    
    @validator('price')
    def validate_price_required(cls, v, values):
        """Validate price is provided for limit orders"""
        if 'order_type' in values and 'limit' in values['order_type'] and not v:
            raise ValueError('Price is required for limit orders')
        return v
    
    @validator('stop_price')
    def validate_stop_price_required(cls, v, values):
        """Validate stop price is provided for stop orders"""
        if 'order_type' in values and 'stop' in values['order_type'] and not v:
            raise ValueError('Stop price is required for stop orders')
        return v
    
    @validator('amount')
    def validate_amount_precision(cls, v):
        """Validate amount precision"""
        if v.as_tuple().exponent < -8:
            raise ValueError('Amount can have maximum 8 decimal places')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "trading_pair": "BTC/USD",
                "order_type": "limit",
                "side": "buy",
                "amount": "0.5",
                "price": "45000.00",
                "time_in_force": "GTC"
            }
        }


class CancelOrderRequest(BaseModel):
    """Cancel an existing order"""
    order_id: str = Field(..., min_length=1, max_length=100, description="Order ID to cancel")
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": "order_123456789"
            }
        }


class ModifyOrderRequest(BaseModel):
    """Modify an existing order"""
    order_id: str = Field(..., min_length=1, max_length=100, description="Order ID")
    amount: Optional[Decimal] = Field(None, gt=0, description="New amount")
    price: Optional[Decimal] = Field(None, gt=0, description="New price")
    
    @validator('amount', 'price')
    def validate_at_least_one(cls, v, values):
        """Ensure at least one field is being updated"""
        if not v and 'amount' not in values and 'price' not in values:
            raise ValueError('Must specify at least one field to modify')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": "order_123456789",
                "price": "46000.00"
            }
        }
