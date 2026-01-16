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
    """Create and execute a new order with trading fees."""


    orders_collection = db.get_collection("orders")
    transactions_collection = db.get_collection("transactions")
    wallets_collection = db.get_collection("wallets")

    # Validate order data
    if order_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    if order_data.price <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than 0")

    # Calculate trading fee
    trading_fee = calculate_trading_fee(order_data.amount, order_data.price)
    total_value = order_data.amount * order_data.price

    # Get user wallet
    wallet = await wallets_collection.find_one({"user_id": user_id})
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found. Please create a wallet first.")

    # Check balance for buy orders
    if order_data.side.lower() == "buy":
        required_amount = total_value + trading_fee
        current_balance = wallet.get("balances", {}).get("USD", 0)

        if current_balance < required_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Required: ${required_amount:.2f} (including ${trading_fee:.2f} fee), Available: ${current_balance:.2f}"
            )

        # Deduct USD from wallet
        await wallets_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    f"balances.USD": current_balance - required_amount,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Add crypto to wallet
        crypto_symbol = order_data.trading_pair.split("/")[0]  # e.g., BTC from BTC/USD
        current_crypto = wallet.get("balances", {}).get(crypto_symbol, 0)
        await wallets_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    f"balances.{crypto_symbol}": current_crypto + order_data.amount,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:  # sell order
        crypto_symbol = order_data.trading_pair.split("/")[0]
        current_crypto = wallet.get("balances", {}).get(crypto_symbol, 0)

        if current_crypto < order_data.amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient {crypto_symbol}. Required: {order_data.amount}, Available: {current_crypto}"
            )

        # Deduct crypto from wallet
        await wallets_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    f"balances.{crypto_symbol}": current_crypto - order_data.amount,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Add USD to wallet (minus fee)
        current_usd = wallet.get("balances", {}).get("USD", 0)
        net_proceeds = total_value - trading_fee
        await wallets_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    f"balances.USD": current_usd + net_proceeds,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    # Create order
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

    # Create trade transaction
    transaction = Transaction(
        user_id=user_id,
        type="trade",
        amount=order_data.amount if order_data.side.lower() == "buy" else -order_data.amount,
        symbol=order_data.trading_pair,
        description=f"{order_data.side.upper()} {order_data.amount} {order_data.trading_pair} @ ${order_data.price}"
    )
    await transactions_collection.insert_one(transaction.dict())

    # Create fee transaction
    fee_transaction = Transaction(
        user_id=user_id,
        type="fee",
        amount=-trading_fee,
        symbol="USD",
        description=f"Trading fee for order {order.id[:8]}"
    )
    await transactions_collection.insert_one(fee_transaction.dict())

    await log_audit(
        db, user_id, "ORDER_CREATED",
        resource=order.id,
        ip_address=request.client.host,
        details={
            "trading_pair": order_data.trading_pair,
            "side": order_data.side,
            "amount": order_data.amount,
            "price": order_data.price,
            "fee": trading_fee
        }
    )

    logger.info(f"✅ Order created: {order.id} - {order_data.side.upper()} {order_data.amount} {order_data.trading_pair} @ ${order_data.price}")

    return {
        "message": "Order created successfully",
        "order": order.dict(),
        "fee": trading_fee,
        "totalCost": total_value + trading_fee if order_data.side.lower() == "buy" else total_value - trading_fee
    }


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
