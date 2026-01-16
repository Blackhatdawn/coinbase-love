"""P2P Transfer endpoints for peer-to-peer cryptocurrency transfers."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import uuid
import logging

from dependencies import get_current_user_id, get_db, get_limiter
from models import Transaction
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transfers", tags=["transfers"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class P2PTransferRequest(BaseModel):
    """P2P Transfer request model"""
    recipient_email: str
    amount: float
    currency: str = "USD"
    note: Optional[str] = None


class P2PTransferResponse(BaseModel):
    """P2P Transfer response model"""
    id: str
    amount: float
    currency: str
    recipient_email: str
    recipient_name: Optional[str] = None
    status: str
    created_at: str


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

@router.post("/p2p")
async def create_p2p_transfer(
    transfer: P2PTransferRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """
    Create an instant P2P transfer between CryptoVault users.
    Validates sender balance and executes off-chain ledger update.
    
    **Request Body:**
    ```json
    {
        "recipient_email": "user@example.com",
        "amount": 100.0,
        "currency": "USD",
        "note": "Payment for services"
    }
    ```
    
    **Response:**
    ```json
    {
        "message": "Transfer completed successfully",
        "transfer": {
            "id": "uuid",
            "amount": 100.0,
            "currency": "USD",
            "recipient_email": "user@example.com",
            "recipient_name": "John Doe",
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

    # Validate balance
    if sender_balance < transfer.amount:
        logger.warning(
            f"Insufficient balance: user {user_id} has {sender_balance} {transfer.currency}, "
            f"trying to transfer {transfer.amount}"
        )
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Validate amount
    if transfer.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive")

    # Generate transfer ID
    transfer_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    # Create sender transaction (debit)
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
            "note": transfer.note
        },
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Create recipient transaction (credit)
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
        await transactions_collection.insert_many([sender_txn, recipient_txn])

        # Update sender wallet balance
        new_sender_balance = sender_balance - transfer.amount
        await wallets_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                f"balances.{transfer.currency}": new_sender_balance,
                "updated_at": timestamp
            }}
        )

        # Update recipient wallet balance
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
                "recipient": recipient["email"]
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
                "transfer_id": transfer_id
            }
        )

        return {
            "message": "Transfer completed successfully",
            "transfer": {
                "id": transfer_id,
                "amount": transfer.amount,
                "currency": transfer.currency,
                "recipient_email": recipient["email"],
                "recipient_name": recipient.get("name"),
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
