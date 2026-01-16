"""Admin dashboard and management endpoints."""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import Optional
import uuid
import csv
from io import StringIO

from dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/setup-first-admin")
async def setup_first_admin(
    request: Request,
    db = Depends(get_db)
):
    """
    Create the first admin user if no admins exist.
    This is a one-time setup endpoint.
    """
    users_collection = db.get_collection("users")
    
    # Check if any admin users already exist
    existing_admin = await users_collection.find_one({"is_admin": True})
    if existing_admin:
        raise HTTPException(
            status_code=400, 
            detail="Admin user already exists. Use regular admin interface to manage users."
        )
    
    body = await request.json()
    email = body.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Find user by email
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please create an account first, then use this endpoint.")
    
    if not user.get("email_verified"):
        raise HTTPException(status_code=400, detail="Email must be verified before becoming admin")
    
    # Make user an admin
    await users_collection.update_one(
        {"id": user["id"]},
        {"$set": {"is_admin": True}}
    )
    
    return {
        "message": "User has been granted admin privileges",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": True
        }
    }


async def is_admin(user_id: str = Depends(get_current_user_id), db = Depends(get_db)) -> bool:
    """Check if user is an admin."""
    users_collection = db.get_collection("users")
    user = await users_collection.find_one({"id": user_id})
    
    if not user or not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return True


@router.get("/stats")
async def get_admin_stats(
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Get platform statistics for admin dashboard."""
    users_collection = db.get_collection("users")
    orders_collection = db.get_collection("orders")
    portfolios_collection = db.get_collection("portfolios")
    
    # Get user stats
    total_users = await users_collection.count_documents({})
    verified_users = await users_collection.count_documents({"email_verified": True})
    
    # Get trading stats (last 24h)
    yesterday = datetime.utcnow() - timedelta(days=1)
    trades_24h = await orders_collection.count_documents({
        "created_at": {"$gte": yesterday}
    })
    
    # Calculate total trading volume (last 24h)
    pipeline = [
        {"$match": {"created_at": {"$gte": yesterday}}},
        {"$group": {"_id": None, "total": {"$sum": {"$multiply": ["$amount", "$price"]}}}}
    ]
    volume_result = await orders_collection.aggregate(pipeline).to_list(1)
    volume_24h = volume_result[0]["total"] if volume_result else 0
    
    # Active users (logged in last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = await users_collection.count_documents({
        "last_login": {"$gte": week_ago}
    })
    
    return {
        "users": {
            "total": total_users,
            "verified": verified_users,
            "active_7d": active_users
        },
        "trading": {
            "trades_24h": trades_24h,
            "volume_24h": round(volume_24h, 2)
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/users")
async def get_users(
    skip: int = 0,
    limit: int = 50,
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Get list of users (paginated)."""
    users_collection = db.get_collection("users")
    
    users = await users_collection.find(
        {},
        {"password_hash": 0, "two_factor_secret": 0, "backup_codes": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await users_collection.count_documents({})
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/trades")
async def get_trades(
    skip: int = 0,
    limit: int = 100,
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Get list of recent trades (paginated)."""
    orders_collection = db.get_collection("orders")
    
    trades = await orders_collection.find({}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await orders_collection.count_documents({})
    
    return {
        "trades": trades,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Get audit logs with optional filters."""
    audit_collection = db.get_collection("audit_logs")
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    
    logs = await audit_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    total = await audit_collection.count_documents(query)
    
    return {
        "logs": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/withdrawals")
async def get_pending_withdrawals(
    skip: int = 0,
    limit: int = 50,
    status: str = "pending",
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Get withdrawal requests for admin review."""
    withdrawals_collection = db.get_collection("withdrawals")
    users_collection = db.get_collection("users")
    
    query = {}
    if status:
        query["status"] = status
    
    withdrawals = await withdrawals_collection.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await withdrawals_collection.count_documents(query)
    
    # Enrich with user information
    for withdrawal in withdrawals:
        user = await users_collection.find_one({"id": withdrawal["user_id"]})
        if user:
            withdrawal["user_email"] = user.get("email")
            withdrawal["user_name"] = user.get("name")
    
    return {
        "withdrawals": withdrawals,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/withdrawals/{withdrawal_id}/approve")
async def approve_withdrawal(
    withdrawal_id: str,
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Approve a withdrawal request (changes status to processing)."""
    withdrawals_collection = db.get_collection("withdrawals")
    
    withdrawal = await withdrawals_collection.find_one({"id": withdrawal_id})
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal["status"] != "pending":
        raise HTTPException(status_code=400, detail="Only pending withdrawals can be approved")
    
    await withdrawals_collection.update_one(
        {"id": withdrawal_id},
        {
            "$set": {
                "status": "processing",
                "processed_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Withdrawal approved and is now processing"}


@router.post("/withdrawals/{withdrawal_id}/complete")
async def complete_withdrawal(
    withdrawal_id: str,
    request: Request,
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Mark withdrawal as completed with transaction hash."""
    body = await request.json()
    transaction_hash = body.get("transaction_hash")
    
    if not transaction_hash:
        raise HTTPException(status_code=400, detail="Transaction hash is required")
    
    withdrawals_collection = db.get_collection("withdrawals")
    
    withdrawal = await withdrawals_collection.find_one({"id": withdrawal_id})
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal["status"] not in ["pending", "processing"]:
        raise HTTPException(status_code=400, detail="Only pending or processing withdrawals can be completed")
    
    await withdrawals_collection.update_one(
        {"id": withdrawal_id},
        {
            "$set": {
                "status": "completed",
                "transaction_hash": transaction_hash,
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    # Update transaction record
    transactions_collection = db.get_collection("transactions")
    await transactions_collection.update_one(
        {"reference": withdrawal_id, "type": "withdrawal"},
        {
            "$set": {
                "status": "completed",
                "transaction_hash": transaction_hash
            }
        }
    )
    
    return {"message": "Withdrawal marked as completed", "transaction_hash": transaction_hash}


@router.post("/withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(
    withdrawal_id: str,
    request: Request,
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """Reject a withdrawal request and refund the user."""
    body = await request.json()
    reason = body.get("reason", "Withdrawal rejected by administrator")
    
    withdrawals_collection = db.get_collection("withdrawals")
    
    withdrawal = await withdrawals_collection.find_one({"id": withdrawal_id})
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal["status"] != "pending":
        raise HTTPException(status_code=400, detail="Only pending withdrawals can be rejected")
    
    # Refund the user's wallet
    wallets_collection = db.get_collection("wallets")
    wallet = await wallets_collection.find_one({"user_id": withdrawal["user_id"]})
    
    if wallet:
        currency = withdrawal["currency"]
        total_amount = withdrawal.get("total_amount", withdrawal["amount"] + withdrawal["fee"])
        current_balance = wallet.get("balances", {}).get(currency, 0)
        
        await wallets_collection.update_one(
            {"user_id": withdrawal["user_id"]},
            {
                "$set": {
                    f"balances.{currency}": current_balance + total_amount,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    # Update withdrawal status
    await withdrawals_collection.update_one(
        {"id": withdrawal_id},
        {
            "$set": {
                "status": "cancelled",
                "notes": reason,
                "processed_at": datetime.utcnow()
            }
        }
    )
    
    # Update transaction records
    transactions_collection = db.get_collection("transactions")
    await transactions_collection.update_many(
        {"reference": withdrawal_id},
        {
            "$set": {
                "status": "cancelled"
            }
        }
    )
    
    # Create refund transaction
    await transactions_collection.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": withdrawal["user_id"],
        "type": "refund",
        "amount": withdrawal["amount"] + withdrawal["fee"],
        "currency": withdrawal["currency"],
        "status": "completed",
        "reference": withdrawal_id,
        "description": f"Refund for rejected withdrawal: {reason}",
        "created_at": datetime.utcnow()
    })
    
    return {"message": "Withdrawal rejected and user refunded", "reason": reason}
