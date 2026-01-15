"""Wallet and deposit management endpoints."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from dependencies import get_current_user_id, get_db, get_limiter
from nowpayments_service import nowpayments_service, PaymentStatus
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wallet", tags=["wallet"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class DepositRequest(BaseModel):
    amount: float
    currency: str = "btc"  # Pay currency (BTC, ETH, etc.)


class WithdrawRequest(BaseModel):
    amount: float
    currency: str
    address: str


# ============================================
# HELPER FUNCTIONS
# ============================================

async def log_audit(db, user_id: str, action: str, resource: Optional[str] = None, 
                    ip_address: Optional[str] = None, details: Optional[dict] = None):
    """Log audit event."""
    from models import AuditLog
    
    logger.info(
        f"Audit log: {action}",
        extra={
            "type": "audit_log",
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "ip_address": ip_address
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


# ============================================
# WALLET BALANCE ENDPOINTS
# ============================================

@router.get("/balance")
async def get_wallet_balance(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's wallet balance."""
    wallets_collection = db.get_collection("wallets")
    
    wallet = await wallets_collection.find_one({"user_id": user_id})
    
    if not wallet:
        # Create default wallet
        wallet = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "balances": {"USD": 0.0},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await wallets_collection.insert_one(wallet)
    
    return {
        "wallet": {
            "balances": wallet.get("balances", {"USD": 0.0}),
            "updated_at": wallet.get("updated_at", datetime.utcnow()).isoformat()
        }
    }


# ============================================
# DEPOSIT ENDPOINTS
# ============================================

@router.post("/deposit/create")
async def create_deposit(
    data: DepositRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """
    Create a crypto deposit invoice.
    Uses NOWPayments integration (or mock in development).
    """
    await limiter.limit("10/minute")(request)
    
    # Validate amount
    if data.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum deposit is $10")
    
    if data.amount > 100000:
        raise HTTPException(status_code=400, detail="Maximum deposit is $100,000")
    
    # Validate currency
    valid_currencies = ["btc", "eth", "usdt", "usdc", "ltc", "bnb", "sol"]
    if data.currency.lower() not in valid_currencies:
        raise HTTPException(status_code=400, detail=f"Invalid currency. Supported: {', '.join(valid_currencies)}")
    
    # Generate unique order ID
    order_id = f"DEP-{user_id[:8]}-{str(uuid.uuid4())[:8]}"
    
    # Create payment via NOWPayments
    try:
        # IPN callback URL for webhook notifications
        ipn_callback_url = f"{settings.app_url}/api/wallet/webhook/nowpayments"
        success_url = f"{settings.app_url}/dashboard?deposit=success"
        cancel_url = f"{settings.app_url}/dashboard?deposit=cancelled"
        
        # Get user email for receipt
        users_collection = db.get_collection("users")
        user = await users_collection.find_one({"id": user_id})
        customer_email = user.get("email") if user else None
        
        payment_result = await nowpayments_service.create_payment(
            price_amount=data.amount,
            price_currency="usd",
            pay_currency=data.currency.lower(),
            order_id=order_id,
            order_description=f"CryptoVault Deposit - ${data.amount}",
            ipn_callback_url=ipn_callback_url,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email
        )
        
        if not payment_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=payment_result.get("error", "Failed to create payment")
            )
        
        # Store deposit record
        deposits_collection = db.get_collection("deposits")
        deposit_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "order_id": order_id,
            "payment_id": payment_result.get("payment_id"),
            "amount": data.amount,
            "currency": "USD",
            "pay_currency": data.currency.upper(),
            "pay_amount": payment_result.get("pay_amount"),
            "pay_address": payment_result.get("pay_address"),
            "status": "pending",
            "mock": payment_result.get("mock", False),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "updated_at": datetime.utcnow()
        }
        await deposits_collection.insert_one(deposit_record)
        
        # Log audit
        await log_audit(
            db, user_id, "DEPOSIT_INITIATED",
            resource=order_id,
            ip_address=request.client.host,
            details={"amount": data.amount, "currency": data.currency}
        )
        
        logger.info(f"✅ Deposit created: {order_id} for ${data.amount}")
        
        return {
            "success": True,
            "orderId": order_id,
            "paymentId": payment_result.get("payment_id"),
            "amount": data.amount,
            "currency": data.currency.upper(),
            "payAddress": payment_result.get("pay_address"),
            "payAmount": payment_result.get("pay_amount"),
            "expiresAt": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "qrCode": payment_result.get("qr_code"),
            "mock": payment_result.get("mock", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Deposit creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create deposit")


@router.get("/deposit/{order_id}")
async def get_deposit_status(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get status of a specific deposit."""
    deposits_collection = db.get_collection("deposits")
    
    deposit = await deposits_collection.find_one({
        "order_id": order_id,
        "user_id": user_id
    })
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    # Refresh status from NOWPayments if not mock
    if not deposit.get("mock") and deposit.get("payment_id"):
        try:
            status_result = await nowpayments_service.get_payment_status(deposit["payment_id"])
            if status_result and "payment_status" in status_result:
                new_status = status_result["payment_status"]
                if new_status != deposit["status"]:
                    await deposits_collection.update_one(
                        {"order_id": order_id},
                        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
                    )
                    deposit["status"] = new_status
        except Exception as e:
            logger.warning(f"Failed to refresh deposit status: {e}")
    
    return {
        "deposit": {
            "orderId": deposit["order_id"],
            "amount": deposit["amount"],
            "currency": deposit["currency"],
            "payCurrency": deposit["pay_currency"],
            "payAmount": deposit.get("pay_amount"),
            "payAddress": deposit.get("pay_address"),
            "status": deposit["status"],
            "createdAt": deposit["created_at"].isoformat(),
            "expiresAt": deposit.get("expires_at", "").isoformat() if deposit.get("expires_at") else None
        }
    }


@router.get("/deposits")
async def get_deposit_history(
    skip: int = 0,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's deposit history."""
    deposits_collection = db.get_collection("deposits")
    
    deposits = await deposits_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await deposits_collection.count_documents({"user_id": user_id})
    
    return {
        "deposits": [
            {
                "orderId": d["order_id"],
                "amount": d["amount"],
                "currency": d["currency"],
                "payCurrency": d["pay_currency"],
                "status": d["status"],
                "createdAt": d["created_at"].isoformat()
            }
            for d in deposits
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@router.post("/webhook/nowpayments")
async def nowpayments_webhook(
    request: Request,
    db = Depends(get_db)
):
    """
    Handle NOWPayments IPN (Instant Payment Notification) webhook.
    This is called by NOWPayments when payment status changes.
    """
    try:
        body = await request.body()
        signature = request.headers.get("x-nowpayments-sig", "")
        
        # Verify signature
        if not nowpayments_service.verify_ipn_signature(body, signature):
            logger.warning("Invalid IPN signature received")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse payload
        import json
        payload = json.loads(body)
        
        payment_id = payload.get("payment_id")
        payment_status = payload.get("payment_status")
        order_id = payload.get("order_id")
        actually_paid = payload.get("actually_paid", 0)
        
        logger.info(f"📬 IPN received: {order_id} - {payment_status}")
        
        # Find deposit record
        deposits_collection = db.get_collection("deposits")
        deposit = await deposits_collection.find_one({"order_id": order_id})
        
        if not deposit:
            logger.warning(f"Deposit not found for order: {order_id}")
            return {"status": "ignored", "reason": "Order not found"}
        
        # Update deposit status
        await deposits_collection.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": payment_status,
                    "actually_paid": actually_paid,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # If payment is finished/confirmed, credit the user's wallet
        if payment_status in PaymentStatus.SUCCESS_STATUSES:
            wallets_collection = db.get_collection("wallets")
            user_id = deposit["user_id"]
            amount = deposit["amount"]
            
            # Update or create wallet
            wallet = await wallets_collection.find_one({"user_id": user_id})
            if wallet:
                current_balance = wallet.get("balances", {}).get("USD", 0)
                await wallets_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "balances.USD": current_balance + amount,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            else:
                await wallets_collection.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "balances": {"USD": amount},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
            
            # Create transaction record
            transactions_collection = db.get_collection("transactions")
            await transactions_collection.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": "deposit",
                "amount": amount,
                "currency": "USD",
                "status": "completed",
                "reference": order_id,
                "description": f"Deposit via {deposit['pay_currency']}",
                "created_at": datetime.utcnow()
            })
            
            # Log audit
            await log_audit(
                db, user_id, "DEPOSIT_COMPLETED",
                resource=order_id,
                details={"amount": amount, "payment_status": payment_status}
            )
            
            logger.info(f"✅ Deposit completed: {order_id} - ${amount}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


# ============================================
# WITHDRAWAL ENDPOINTS (placeholder)
# ============================================

@router.post("/withdraw")
async def create_withdrawal(
    data: WithdrawRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Create a withdrawal request (placeholder - requires additional integration)."""
    await limiter.limit("5/minute")(request)
    
    # This would integrate with actual withdrawal processing
    # For now, return a mock response
    raise HTTPException(
        status_code=501, 
        detail="Withdrawals are not yet enabled. Please contact support."
    )
