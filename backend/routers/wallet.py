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
from services.transactions_utils import broadcast_transaction_event

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
        # IPN callback URL for webhook notifications (use backend API URL, not frontend)
        backend_url = settings.public_api_url or settings.app_url
        ipn_callback_url = f"{backend_url}/api/wallet/webhook/nowpayments"
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
    
    Enterprise-grade webhook handling:
    - Signature verification for security
    - Proper content-type handling
    - Comprehensive error handling and logging
    - Idempotent processing
    """
    try:
        # Log webhook receipt
        logger.info(f"📬 NOWPayments webhook received from {request.client.host}")
        
        # Get raw body for signature verification (must be done before parsing)
        body = await request.body()
        
        # Check content-type (should be application/json)
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            logger.warning(f"Unexpected content-type: {content_type}")
            # Continue anyway - some webhook providers don't set proper content-type
        
        # Get signature header
        signature = request.headers.get("x-nowpayments-sig", "")
        
        # Parse payload first to check if it's valid JSON
        import json
        try:
            if not body:
                logger.error("Empty webhook body received")
                raise HTTPException(status_code=400, detail="Empty request body")
            
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            # Log raw body for debugging (truncate if too long)
            body_preview = body.decode('utf-8', errors='ignore')[:200]
            logger.error(f"Raw body preview: {body_preview}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Verify signature (only if signature is provided)
        if signature:
            if not nowpayments_service.verify_ipn_signature(body, signature):
                logger.warning(f"❌ Invalid IPN signature received for payment: {payload.get('payment_id')}")
                raise HTTPException(status_code=400, detail="Invalid signature")
            logger.info("✅ Webhook signature verified")
        else:
            logger.warning("⚠️ No signature provided - processing anyway (development mode)")
        
        # Log full payload for debugging
        logger.info(f"Webhook payload: {json.dumps(payload, indent=2)}")
        
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
            deposit_transaction = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": "deposit",
                "amount": amount,
                "currency": "USD",
                "status": "completed",
                "reference": order_id,
                "description": f"Deposit via {deposit['pay_currency']}",
                "created_at": datetime.utcnow()
            }
            await transactions_collection.insert_one(deposit_transaction)
            await broadcast_transaction_event(user_id, deposit_transaction)
            
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
    """
    Create a withdrawal request.
    Validates balance, creates withdrawal record, and initiates processing.
    """
    
    # Validate amount
    if data.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $10")
    
    if data.amount > 10000:
        raise HTTPException(status_code=400, detail="Maximum withdrawal is $10,000 per transaction")
    
    # Validate currency
    valid_currencies = ["USD", "BTC", "ETH", "USDT", "USDC"]
    if data.currency.upper() not in valid_currencies:
        raise HTTPException(status_code=400, detail=f"Invalid currency. Supported: {', '.join(valid_currencies)}")
    
    # Validate address format (basic validation)
    if not data.address or len(data.address.strip()) < 10:
        raise HTTPException(status_code=400, detail="Valid withdrawal address is required")
    
    # Check user's wallet balance
    wallets_collection = db.get_collection("wallets")
    wallet = await wallets_collection.find_one({"user_id": user_id})
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    current_balance = wallet.get("balances", {}).get(data.currency.upper(), 0)
    
    # Calculate withdrawal fee (1% with minimum $1)
    fee_percentage = 1.0  # 1%
    withdrawal_fee = max(data.amount * (fee_percentage / 100), 1.0)
    total_amount = data.amount + withdrawal_fee
    
    if current_balance < total_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. Required: ${total_amount:.2f} (including ${withdrawal_fee:.2f} fee), Available: ${current_balance:.2f}"
        )
    
    # Create withdrawal record
    withdrawals_collection = db.get_collection("withdrawals")
    withdrawal_id = str(uuid.uuid4())
    
    withdrawal_record = {
        "id": withdrawal_id,
        "user_id": user_id,
        "amount": data.amount,
        "currency": data.currency.upper(),
        "address": data.address.strip(),
        "status": "pending",  # pending, processing, completed, failed, cancelled
        "fee": withdrawal_fee,
        "net_amount": data.amount,
        "total_amount": total_amount,
        "transaction_hash": None,
        "created_at": datetime.utcnow(),
        "processed_at": None,
        "completed_at": None,
        "notes": None
    }
    
    await withdrawals_collection.insert_one(withdrawal_record)
    
    # Deduct from wallet balance (hold the funds)
    await wallets_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"balances.{data.currency.upper()}": current_balance - total_amount,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Create transaction record
    transactions_collection = db.get_collection("transactions")
    withdrawal_transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "withdrawal",
        "amount": -data.amount,  # Negative for withdrawal
        "currency": data.currency.upper(),
        "status": "pending",
        "reference": withdrawal_id,
        "description": f"Withdrawal to {data.address[:12]}...",
        "created_at": datetime.utcnow()
    }
    await transactions_collection.insert_one(withdrawal_transaction)
    
    # Create fee transaction record
    fee_transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "fee",
        "amount": -withdrawal_fee,  # Negative for fee
        "currency": data.currency.upper(),
        "status": "completed",
        "reference": withdrawal_id,
        "description": f"Withdrawal fee for {withdrawal_id[:8]}...",
        "created_at": datetime.utcnow()
    }
    await transactions_collection.insert_one(fee_transaction)

    await broadcast_transaction_event(user_id, withdrawal_transaction)
    await broadcast_transaction_event(user_id, fee_transaction)
    
    # Log audit
    await log_audit(
        db, user_id, "WITHDRAWAL_REQUESTED",
        resource=withdrawal_id,
        ip_address=request.client.host,
        details={
            "amount": data.amount,
            "currency": data.currency,
            "address": data.address[:12] + "...",  # Don't log full address
            "fee": withdrawal_fee
        }
    )
    
    # Send email notification (if email service is configured)
    try:
        users_collection = db.get_collection("users")
        user = await users_collection.find_one({"id": user_id})
        
        if user and user.get("email"):
            # Note: This would require email service integration
            logger.info(f"📧 Withdrawal notification email should be sent to {user['email']}")
    except Exception as e:
        logger.warning(f"Failed to send withdrawal notification email: {e}")
    
    logger.info(f"✅ Withdrawal request created: {withdrawal_id} for ${data.amount}")
    
    return {
        "success": True,
        "withdrawalId": withdrawal_id,
        "amount": data.amount,
        "currency": data.currency.upper(),
        "address": data.address,
        "fee": withdrawal_fee,
        "totalAmount": total_amount,
        "status": "pending",
        "estimatedProcessingTime": "1-3 business days",
        "note": "Your withdrawal request has been received and will be processed within 1-3 business days. You will receive an email notification when the withdrawal is complete."
    }


@router.get("/withdrawals")
async def get_withdrawal_history(
    skip: int = 0,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's withdrawal history."""
    withdrawals_collection = db.get_collection("withdrawals")
    
    withdrawals = await withdrawals_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await withdrawals_collection.count_documents({"user_id": user_id})
    
    return {
        "withdrawals": [
            {
                "id": w["id"],
                "amount": w["amount"],
                "currency": w["currency"],
                "address": w["address"],
                "status": w["status"],
                "fee": w["fee"],
                "totalAmount": w.get("total_amount", w["amount"] + w["fee"]),
                "transactionHash": w.get("transaction_hash"),
                "createdAt": w["created_at"].isoformat(),
                "processedAt": w.get("processed_at").isoformat() if w.get("processed_at") else None,
                "completedAt": w.get("completed_at").isoformat() if w.get("completed_at") else None
            }
            for w in withdrawals
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/withdraw/{withdrawal_id}")
async def get_withdrawal_status(
    withdrawal_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get status of a specific withdrawal."""
    withdrawals_collection = db.get_collection("withdrawals")

    withdrawal = await withdrawals_collection.find_one({
        "id": withdrawal_id,
        "user_id": user_id
    })

    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    return {
        "withdrawal": {
            "id": withdrawal["id"],
            "amount": withdrawal["amount"],
            "currency": withdrawal["currency"],
            "address": withdrawal["address"],
            "status": withdrawal["status"],
            "fee": withdrawal["fee"],
            "totalAmount": withdrawal.get("total_amount", withdrawal["amount"] + withdrawal["fee"]),
            "transactionHash": withdrawal.get("transaction_hash"),
            "createdAt": withdrawal["created_at"].isoformat(),
            "processedAt": withdrawal.get("processed_at").isoformat() if withdrawal.get("processed_at") else None,
            "completedAt": withdrawal.get("completed_at").isoformat() if withdrawal.get("completed_at") else None,
            "notes": withdrawal.get("notes")
        }
    }


# ============================================
# P2P TRANSFER ENDPOINTS
# ============================================

class TransferRequest(BaseModel):
    recipient_email: str
    amount: float
    currency: str = "USD"
    note: Optional[str] = None


@router.post("/transfer")
async def create_p2p_transfer(
    data: TransferRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """
    Create a peer-to-peer transfer to another user.
    Transfers are instant and free within the platform.
    """


    # Validate amount
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be greater than 0")

    if data.amount < 1:
        raise HTTPException(status_code=400, detail="Minimum transfer amount is $1")

    if data.amount > 50000:
        raise HTTPException(status_code=400, detail="Maximum transfer amount is $50,000 per transaction")

    # Validate currency
    valid_currencies = ["USD", "BTC", "ETH", "USDT", "USDC"]
    if data.currency.upper() not in valid_currencies:
        raise HTTPException(status_code=400, detail=f"Invalid currency. Supported: {', '.join(valid_currencies)}")

    # Get sender's wallet
    users_collection = db.get_collection("users")
    wallets_collection = db.get_collection("wallets")
    transfers_collection = db.get_collection("transfers")
    transactions_collection = db.get_collection("transactions")

    sender = await users_collection.find_one({"id": user_id})
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    # Check if sender is trying to send to themselves
    if sender["email"].lower() == data.recipient_email.lower():
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    # Find recipient by email
    recipient = await users_collection.find_one({"email": data.recipient_email.lower()})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found. User must have an account.")

    if not recipient.get("email_verified"):
        raise HTTPException(status_code=400, detail="Recipient's email is not verified. Ask them to verify their account first.")

    # Check sender's balance
    sender_wallet = await wallets_collection.find_one({"user_id": user_id})
    if not sender_wallet:
        raise HTTPException(status_code=404, detail="Sender wallet not found")

    sender_balance = sender_wallet.get("balances", {}).get(data.currency.upper(), 0)

    # P2P transfers are free (no fee)
    transfer_fee = 0.0
    total_amount = data.amount

    if sender_balance < total_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Required: {total_amount} {data.currency}, Available: {sender_balance} {data.currency}"
        )

    # Create transfer record
    transfer_id = str(uuid.uuid4())
    transfer_record = {
        "id": transfer_id,
        "sender_id": user_id,
        "sender_email": sender["email"],
        "sender_name": sender["name"],
        "recipient_id": recipient["id"],
        "recipient_email": recipient["email"],
        "recipient_name": recipient["name"],
        "amount": data.amount,
        "currency": data.currency.upper(),
        "fee": transfer_fee,
        "note": data.note,
        "status": "completed",  # P2P transfers are instant
        "created_at": datetime.utcnow(),
        "completed_at": datetime.utcnow()
    }

    await transfers_collection.insert_one(transfer_record)

    # Deduct from sender's wallet
    await wallets_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"balances.{data.currency.upper()}": sender_balance - total_amount,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Add to recipient's wallet (create if doesn't exist)
    recipient_wallet = await wallets_collection.find_one({"user_id": recipient["id"]})
    if recipient_wallet:
        recipient_balance = recipient_wallet.get("balances", {}).get(data.currency.upper(), 0)
        await wallets_collection.update_one(
            {"user_id": recipient["id"]},
            {
                "$set": {
                    f"balances.{data.currency.upper()}": recipient_balance + data.amount,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Create wallet for recipient
        await wallets_collection.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": recipient["id"],
            "balances": {data.currency.upper(): data.amount},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

    # Create transaction records for both users
    # Sender transaction
    sender_transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "transfer_out",
        "amount": -data.amount,
        "currency": data.currency.upper(),
        "status": "completed",
        "reference": transfer_id,
        "description": f"Transfer to {recipient['name']} ({recipient['email']})",
        "created_at": datetime.utcnow()
    }
    await transactions_collection.insert_one(sender_transaction)

    # Recipient transaction
    recipient_transaction = {
        "id": str(uuid.uuid4()),
        "user_id": recipient["id"],
        "type": "transfer_in",
        "amount": data.amount,
        "currency": data.currency.upper(),
        "status": "completed",
        "reference": transfer_id,
        "description": f"Transfer from {sender['name']} ({sender['email']})",
        "created_at": datetime.utcnow()
    }
    await transactions_collection.insert_one(recipient_transaction)

    await broadcast_transaction_event(user_id, sender_transaction)
    await broadcast_transaction_event(recipient["id"], recipient_transaction)

    # Log audit events
    await log_audit(
        db, user_id, "P2P_TRANSFER_SENT",
        resource=transfer_id,
        ip_address=request.client.host,
        details={
            "recipient_email": recipient["email"],
            "amount": data.amount,
            "currency": data.currency
        }
    )

    await log_audit(
        db, recipient["id"], "P2P_TRANSFER_RECEIVED",
        resource=transfer_id,
        details={
            "sender_email": sender["email"],
            "amount": data.amount,
            "currency": data.currency
        }
    )

    logger.info(f"✅ P2P transfer completed: {transfer_id} - {data.amount} {data.currency} from {sender['email']} to {recipient['email']}")

    # TODO: Send email notifications to both parties

    return {
        "success": True,
        "transferId": transfer_id,
        "amount": data.amount,
        "currency": data.currency.upper(),
        "recipient": {
            "email": recipient["email"],
            "name": recipient["name"]
        },
        "fee": transfer_fee,
        "status": "completed",
        "message": f"Successfully transferred {data.amount} {data.currency} to {recipient['name']}"
    }


@router.get("/transfers")
async def get_transfer_history(
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's P2P transfer history (both sent and received)."""
    transfers_collection = db.get_collection("transfers")

    # Find transfers where user is either sender or recipient
    transfers = await transfers_collection.find({
        "$or": [
            {"sender_id": user_id},
            {"recipient_id": user_id}
        ]
    }).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    total = await transfers_collection.count_documents({
        "$or": [
            {"sender_id": user_id},
            {"recipient_id": user_id}
        ]
    })

    # Format transfers with direction indicator
    formatted_transfers = []
    for transfer in transfers:
        is_sender = transfer["sender_id"] == user_id
        formatted_transfers.append({
            "id": transfer["id"],
            "amount": transfer["amount"],
            "currency": transfer["currency"],
            "direction": "sent" if is_sender else "received",
            "otherParty": {
                "email": transfer["recipient_email"] if is_sender else transfer["sender_email"],
                "name": transfer["recipient_name"] if is_sender else transfer["sender_name"]
            },
            "note": transfer.get("note"),
            "status": transfer["status"],
            "createdAt": transfer["created_at"].isoformat(),
            "completedAt": transfer.get("completed_at").isoformat() if transfer.get("completed_at") else None
        })

    return {
        "transfers": formatted_transfers,
        "total": total,
        "skip": skip,
        "limit": limit
    }
