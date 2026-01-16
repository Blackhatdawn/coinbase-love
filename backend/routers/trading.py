"""Trading and order management endpoints with fee system and advanced order types."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import logging
import uuid

from models import Order, OrderCreate, Transaction
from dependencies import get_current_user_id, get_db, get_limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["trading"])

# Trading fee configuration
TRADING_FEE_PERCENTAGE = 0.1  # 0.1% trading fee
MIN_TRADING_FEE = 0.01  # Minimum $0.01 fee


def calculate_trading_fee(amount: float, price: float, fee_percentage: float = TRADING_FEE_PERCENTAGE) -> float:
    """Calculate trading fee with minimum fee threshold."""
    total_value = amount * price
    fee = total_value * (fee_percentage / 100)
    return max(fee, MIN_TRADING_FEE)


# Enhanced order models for advanced order types
class AdvancedOrderCreate(BaseModel):
    trading_pair: str
    order_type: str  # market, limit, stop_loss, take_profit, stop_limit
    side: str  # buy, sell
    amount: float = Field(gt=0)
    price: Optional[float] = Field(default=None, gt=0)
    stop_price: Optional[float] = Field(default=None, gt=0)  # For stop orders
    time_in_force: Optional[str] = Field(default="GTC")  # GTC, IOC, FOK, GTD
    expire_time: Optional[datetime] = None  # For GTD orders


async def log_audit(db, user_id, action, resource=None, ip_address=None, details=None, request_id=None):
    """Log audit event."""
    from models import AuditLog

    logger.info(
        f"Audit log: {action}",
        extra={
            "type": "audit_log",
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "ip_address": ip_address,
            "request_id": request_id
        }
    )

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        details=details
    )
    await db.get_collection("audit_logs").insert_one(audit_log.dict())


@router.get("")
async def get_orders(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's order history."""
    orders_collection = db.get_collection("orders")
    orders = await orders_collection.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    return {"orders": orders}


@router.post("")
async def create_order(
    order_data: OrderCreate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Create and execute a new order."""
    
    
    orders_collection = db.get_collection("orders")
    transactions_collection = db.get_collection("transactions")

    order = Order(
        user_id=user_id,
        trading_pair=order_data.trading_pair,
        order_type=order_data.order_type,
        side=order_data.side,
        amount=order_data.amount,
        price=order_data.price,
        status="filled",
        filled_at=datetime.utcnow()
    )

    await orders_collection.insert_one(order.dict())

    transaction = Transaction(
        user_id=user_id,
        type="trade",
        amount=order_data.amount,
        symbol=order_data.trading_pair,
        description=f"{order_data.side.upper()} {order_data.amount} {order_data.trading_pair} @ {order_data.price}"
    )
    await transactions_collection.insert_one(transaction.dict())

    await log_audit(
        db, user_id, "ORDER_CREATED", 
        resource=order.id, 
        ip_address=request.client.host
    )

    return {"message": "Order created successfully", "order": order.dict()}


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get specific order by ID."""
    orders_collection = db.get_collection("orders")
    order = await orders_collection.find_one({"id": order_id, "user_id": user_id})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"order": order}
