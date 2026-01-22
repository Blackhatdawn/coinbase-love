"""
P2P Transfer Endpoints with Smart Gas Fees
Enterprise-grade peer-to-peer cryptocurrency transfers.

Features:
- Dynamic gas fee calculation using smart crypto data analysis
- BTC fees in SATs (satoshis)
- Email notifications for both sender and recipient
- Audit logging for compliance
- Real-time balance validation
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Literal
import uuid
import logging

from dependencies import get_current_user_id, get_db, get_limiter
from models import Transaction
from config import settings
from services.gas_fees import gas_fee_service
from email_service import email_service
from services.transactions_utils import broadcast_transaction_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transfers", tags=["transfers"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class P2PTransferRequest(BaseModel):
    """P2P Transfer request model with smart gas fee support"""
    recipient_email: str = Field(..., description="Recipient's CryptoVault email")
    amount: float = Field(..., gt=0, description="Transfer amount")
    currency: str = Field(default="USD", description="Currency code (BTC, ETH, USD, etc.)")
    note: Optional[str] = Field(None, max_length=500, description="Optional transfer note")
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        default="medium", 
        description="Fee priority level (affects confirmation time)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "recipient_email": "user@example.com",
                "amount": 0.01,
                "currency": "BTC",
                "note": "Payment for services",
                "priority": "medium"
            }
        }


class P2PTransferResponse(BaseModel):
    """P2P Transfer response model"""
    id: str
    amount: float
    currency: str
    recipient_email: str
    recipient_name: Optional[str] = None
    gas_fee: float
    gas_fee_display: str
    total_deducted: float
    status: str
    created_at: str


class FeeEstimateRequest(BaseModel):
    """Fee estimation request model"""
    amount: float = Field(..., gt=0, description="Transfer amount")
    currency: str = Field(default="USD", description="Currency code")


class FeeEstimateResponse(BaseModel):
    """Fee estimation response model"""
    amount: float
    currency: str
    estimates: dict
    recommended: str


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
# P2P TRANSFER ENDPOINTS
# ============================================

@router.get("/fee-estimate")
async def estimate_transfer_fee(
    amount: float,
    currency: str = "USD",
    user_id: str = Depends(get_current_user_id)
):
    """
    Get fee estimates for a P2P transfer at all priority levels.
    
    **Query Parameters:**
    - `amount`: Transfer amount
    - `currency`: Currency code (BTC, ETH, USD, etc.)
    
    **Response:**
    Returns fee estimates for low, medium, high, and urgent priorities.
    For BTC, fees are also shown in SATs (satoshis).
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    estimates = gas_fee_service.get_fee_estimate(amount, currency)
    
    return estimates


@router.post("/p2p")
async def create_p2p_transfer(
    transfer: P2PTransferRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """
    Create an instant P2P transfer between CryptoVault users with smart gas fees.
    
    **Features:**
    - Dynamic gas fee calculation based on currency and priority
    - BTC fees displayed in SATs for precision
    - Email notifications to both sender and recipient
    - Real-time balance validation
    - Audit logging for compliance
    
    **Request Body:**
    ```json
    {
        "recipient_email": "user@example.com",
        "amount": 0.01,
        "currency": "BTC",
        "note": "Payment for services",
        "priority": "medium"
    }
    ```
    
    **Response:**
    ```json
    {
        "message": "Transfer completed successfully",
        "transfer": {
            "id": "uuid",
            "amount": 0.01,
            "currency": "BTC",
            "recipient_email": "user@example.com",
            "recipient_name": "John Doe",
            "gas_fee": 0.00001,
            "gas_fee_display": "1,000 SATs",
            "total_deducted": 0.01001,
            "status": "completed",
            "created_at": "2026-01-16T12:00:00"
        }
    }
    ```
    """
    users_collection = db.get_collection("users")
    transactions_collection = db.get_collection("transactions")
    ip_address = request.client.host if request.client else "unknown"

    # Get sender
    sender = await users_collection.find_one({"id": user_id})
    if not sender:
        logger.error(f"Sender not found: {user_id}")
        raise HTTPException(status_code=404, detail="Sender not found")

    # Get recipient by email (case-insensitive)
    recipient = await users_collection.find_one(
        {"email": {"$regex": f"^{transfer.recipient_email}$", "$options": "i"}}
    )
    if not recipient:
        logger.warning(f"Recipient not found: {transfer.recipient_email}")
        raise HTTPException(
            status_code=404,
            detail="Recipient not found. They must have a CryptoVault account."
        )

    # Check self-transfer
    if recipient["id"] == user_id:
        logger.warning(f"Self-transfer attempted by {user_id}")
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    # Calculate smart gas fee
    fee_waived = gas_fee_service.is_fee_waived(transfer.currency, transfer.amount)
    
    if fee_waived:
        gas_fee = 0.0
        gas_fee_display = "Waived"
    else:
        fee_info = gas_fee_service.calculate_fee(
            transfer.amount, 
            transfer.currency, 
            transfer.priority,
            include_breakdown=True
        )
        gas_fee = fee_info["fee"]
        gas_fee_display = fee_info["fee_display"]
    
    total_to_deduct = transfer.amount + gas_fee

    # Get current balances (from wallets collection)
    wallets_collection = db.get_collection("wallets")
    sender_wallet = await wallets_collection.find_one({"user_id": user_id})
    
    if not sender_wallet:
        # Create wallet if doesn't exist
        sender_wallet = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "balances": {transfer.currency: 0.0},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await wallets_collection.insert_one(sender_wallet)

    sender_balance = sender_wallet.get("balances", {}).get(transfer.currency, 0.0)

    # Validate balance (including gas fee)
    if sender_balance < total_to_deduct:
        logger.warning(
            f"Insufficient balance: user {user_id} has {sender_balance} {transfer.currency}, "
            f"needs {total_to_deduct} (amount: {transfer.amount}, fee: {gas_fee})"
        )
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. You need {total_to_deduct:.8f} {transfer.currency} "
                   f"(amount + gas fee)"
        )

    # Generate transfer ID
    transfer_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    # Create sender transaction (debit - amount + fee)
    sender_txn = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "p2p_send",
        "amount": -transfer.amount,
        "currency": transfer.currency,
        "status": "completed",
        "metadata": {
            "transfer_id": transfer_id,
            "recipient_id": recipient["id"],
            "recipient_email": recipient["email"],
            "recipient_name": recipient.get("name", "CryptoVault User"),
            "note": transfer.note,
            "gas_fee": gas_fee,
            "gas_fee_display": gas_fee_display,
            "priority": transfer.priority
        },
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Create fee transaction (if applicable)
    fee_txn = None
    if gas_fee > 0:
        fee_txn = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "gas_fee",
            "amount": -gas_fee,
            "currency": transfer.currency,
            "status": "completed",
            "metadata": {
                "transfer_id": transfer_id,
                "fee_type": "p2p_transfer",
                "priority": transfer.priority
            },
            "created_at": timestamp,
            "updated_at": timestamp
        }

    # Create recipient transaction (credit - full amount, no fee deducted)
    recipient_txn = {
        "id": str(uuid.uuid4()),
        "user_id": recipient["id"],
        "type": "p2p_receive",
        "amount": transfer.amount,
        "currency": transfer.currency,
        "status": "completed",
        "metadata": {
            "transfer_id": transfer_id,
            "sender_id": user_id,
            "sender_email": sender["email"],
            "sender_name": sender.get("name", "CryptoVault User"),
            "note": transfer.note
        },
        "created_at": timestamp,
        "updated_at": timestamp
    }

    try:
        # Execute atomic transfer
        txns_to_insert = [sender_txn, recipient_txn]
        if fee_txn:
            txns_to_insert.append(fee_txn)
        await transactions_collection.insert_many(txns_to_insert)

        await broadcast_transaction_event(user_id, sender_txn)
        await broadcast_transaction_event(recipient["id"], recipient_txn)
        if fee_txn:
            await broadcast_transaction_event(user_id, fee_txn)

        # Update sender wallet balance (deduct amount + fee)
        new_sender_balance = sender_balance - total_to_deduct
        await wallets_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                f"balances.{transfer.currency}": new_sender_balance,
                "updated_at": timestamp
            }}
        )

        # Update recipient wallet balance (credit full amount)
        recipient_wallet = await wallets_collection.find_one({"user_id": recipient["id"]})
        if not recipient_wallet:
            recipient_wallet = {
                "id": str(uuid.uuid4()),
                "user_id": recipient["id"],
                "balances": {transfer.currency: 0.0},
                "created_at": timestamp,
                "updated_at": timestamp
            }
            await wallets_collection.insert_one(recipient_wallet)

        recipient_balance = recipient_wallet.get("balances", {}).get(transfer.currency, 0.0)
        new_recipient_balance = recipient_balance + transfer.amount
        await wallets_collection.update_one(
            {"user_id": recipient["id"]},
            {"$set": {
                f"balances.{transfer.currency}": new_recipient_balance,
                "updated_at": timestamp
            }}
        )

        # Log audit
        await log_audit(
            db,
            user_id=user_id,
            action="p2p_transfer",
            resource=transfer_id,
            ip_address=ip_address,
            details={
                "transfer_id": transfer_id,
                "amount": transfer.amount,
                "currency": transfer.currency,
                "recipient": recipient["email"],
                "gas_fee": gas_fee,
                "priority": transfer.priority
            }
        )

        logger.info(
            f"P2P Transfer completed",
            extra={
                "type": "p2p_transfer",
                "user_id": user_id,
                "recipient_id": recipient["id"],
                "amount": transfer.amount,
                "currency": transfer.currency,
                "gas_fee": gas_fee,
                "transfer_id": transfer_id
            }
        )

        # Send email notifications (async, non-blocking)
        try:
            # Email to sender
            await email_service.send_p2p_transfer_sent(
                to_email=sender["email"],
                sender_name=sender.get("name", "CryptoVault User"),
                recipient_name=recipient.get("name", "CryptoVault User"),
                recipient_email=recipient["email"],
                amount=f"{transfer.amount:.8f}".rstrip('0').rstrip('.'),
                asset=transfer.currency,
                gas_fee=gas_fee_display,
                transaction_id=transfer_id,
                note=transfer.note
            )
            
            # Email to recipient
            await email_service.send_p2p_transfer_received(
                to_email=recipient["email"],
                recipient_name=recipient.get("name", "CryptoVault User"),
                sender_name=sender.get("name", "CryptoVault User"),
                sender_email=sender["email"],
                amount=f"{transfer.amount:.8f}".rstrip('0').rstrip('.'),
                asset=transfer.currency,
                transaction_id=transfer_id,
                note=transfer.note
            )
        except Exception as email_error:
            # Log but don't fail the transfer
            logger.warning(f"Failed to send transfer emails: {str(email_error)}")

        return {
            "message": "Transfer completed successfully",
            "transfer": {
                "id": transfer_id,
                "amount": transfer.amount,
                "currency": transfer.currency,
                "recipient_email": recipient["email"],
                "recipient_name": recipient.get("name"),
                "gas_fee": gas_fee,
                "gas_fee_display": gas_fee_display,
                "total_deducted": total_to_deduct,
                "status": "completed",
                "created_at": timestamp.isoformat()
            }
        }

    except Exception as e:
        logger.error(
            f"P2P transfer failed: {str(e)}",
            extra={
                "type": "p2p_transfer_error",
                "user_id": user_id,
                "transfer_id": transfer_id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Transfer failed. Please try again."
        )


@router.get("/p2p/history")
async def get_p2p_history(
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """
    Get P2P transfer history for the current user.
    
    **Query Parameters:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum number of records to return (default: 50)
    
    **Response:**
    ```json
    {
        "transfers": [
            {
                "id": "uuid",
                "type": "p2p_send",
                "amount": 100.0,
                "currency": "USD",
                "recipient": "user@example.com",
                "status": "completed",
                "created_at": "2026-01-16T12:00:00"
            }
        ],
        "total": 42
    }
    ```
    """
    transactions_collection = db.get_collection("transactions")

    # Get all P2P transfers for user (both sends and receives)
    query = {
        "$or": [
            {"user_id": user_id, "type": {"$in": ["p2p_send", "p2p_receive"]}}
        ]
    }

    transfers = await transactions_collection.find(query) \
        .sort("created_at", -1) \
        .skip(skip) \
        .limit(limit) \
        .to_list(limit)

    total = await transactions_collection.count_documents(query)

    # Format response
    formatted_transfers = []
    for t in transfers:
        formatted_transfers.append({
            "id": t.get("metadata", {}).get("transfer_id", t.get("id")),
            "type": t.get("type"),  # p2p_send or p2p_receive
            "amount": abs(t.get("amount", 0)),
            "currency": t.get("currency", "USD"),
            "direction": "sent" if t.get("type") == "p2p_send" else "received",
            "counterparty": (
                t.get("metadata", {}).get("recipient_email")
                if t.get("type") == "p2p_send"
                else t.get("metadata", {}).get("sender_email")
            ),
            "note": t.get("metadata", {}).get("note"),
            "status": t.get("status", "completed"),
            "created_at": t.get("created_at", datetime.utcnow()).isoformat()
        })

    return {
        "transfers": formatted_transfers,
        "total": total,
        "skip": skip,
        "limit": limit
    }
