"""Admin dashboard and management endpoints."""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
import csv
from io import StringIO

from dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/admin", tags=["admin"])


def percent_change(previous: float, current: float) -> float:
    """Calculate percentage change with zero-safe handling."""
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100


def normalize_audit_log(log: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize audit log fields for consistent export/response."""
    if "_id" in log:
        log["_id"] = str(log["_id"])
    if "timestamp" not in log and "created_at" in log:
        log["timestamp"] = log["created_at"]
    return log


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
    alerts_collection = db.get_collection("price_alerts")
    
    # Get user stats
    total_users = await users_collection.count_documents({})
    verified_users = await users_collection.count_documents({"email_verified": True})
    
    # Get trading stats (last 24h)
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    day_before = now - timedelta(days=2)
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
    
    # Calculate previous 24h volume for change percentage
    previous_volume_pipeline = [
        {
            "$match": {
                "created_at": {
                    "$gte": day_before,
                    "$lt": yesterday
                }
            }
        },
        {"$group": {"_id": None, "total": {"$sum": {"$multiply": ["$amount", "$price"]}}}}
    ]
    previous_volume_result = await orders_collection.aggregate(previous_volume_pipeline).to_list(1)
    previous_volume_24h = previous_volume_result[0]["total"] if previous_volume_result else 0

    # Active users (logged in last 7 days)
    week_ago = now - timedelta(days=7)
    active_users = await users_collection.count_documents({
        "last_login": {"$gte": week_ago}
    })

    # User growth (last 7 days vs previous 7 days)
    previous_week = now - timedelta(days=14)
    new_users_current = await users_collection.count_documents({
        "created_at": {"$gte": week_ago}
    })
    new_users_previous = await users_collection.count_documents({
        "created_at": {"$gte": previous_week, "$lt": week_ago}
    })

    # Active alerts
    total_alerts = await alerts_collection.count_documents({"is_active": True})

    user_growth = percent_change(new_users_previous, new_users_current)
    volume_change = percent_change(previous_volume_24h, volume_24h)
    
    return {
        "totalUsers": total_users,
        "activeUsers": active_users,
        "volume24h": round(volume_24h, 2),
        "totalAlerts": total_alerts,
        "userGrowth": round(user_growth, 2),
        "volumeChange": round(volume_change, 2),
        "users": {
            "total": total_users,
            "verified": verified_users,
            "active_7d": active_users
        },
        "trading": {
            "trades_24h": trades_24h,
            "volume_24h": round(volume_24h, 2)
        },
        "timestamp": now.isoformat()
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
    wallets_collection = db.get_collection("wallets")
    
    users = await users_collection.find(
        {},
        {"password_hash": 0, "two_factor_secret": 0, "backup_codes": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await users_collection.count_documents({})

    user_ids = [user.get("id") for user in users if user.get("id")]
    wallets = []
    if user_ids:
        wallets = await wallets_collection.find({"user_id": {"$in": user_ids}}).to_list(len(user_ids))
    wallets_by_user = {wallet.get("user_id"): wallet for wallet in wallets}

    formatted_users = []
    now = datetime.utcnow()
    for user in users:
        wallet = wallets_by_user.get(user.get("id"), {})
        balances = wallet.get("balances", {}) if wallet else {}
        usd_balance = balances.get("USD", 0.0)

        status = "active"
        if not user.get("email_verified"):
            status = "pending"
        locked_until = user.get("locked_until")
        if locked_until and locked_until > now:
            status = "suspended"

        created_at = user.get("created_at")
        last_login = user.get("last_login")

        formatted_users.append({
            "id": user.get("id"),
            "email": user.get("email"),
            "name": user.get("name", ""),
            "status": status,
            "balance": float(usd_balance) if usd_balance is not None else 0.0,
            "joinedAt": created_at.isoformat() if hasattr(created_at, "isoformat") else None,
            "lastLogin": last_login.isoformat() if hasattr(last_login, "isoformat") else None,
            "is_admin": user.get("is_admin", False)
        })
    
    return {
        "users": formatted_users,
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
    users_collection = db.get_collection("users")
    
    trades = await orders_collection.find({}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await orders_collection.count_documents({})

    user_ids = [trade.get("user_id") for trade in trades if trade.get("user_id")]
    users = []
    if user_ids:
        users = await users_collection.find(
            {"id": {"$in": list(set(user_ids))}},
            {"id": 1, "email": 1}
        ).to_list(len(set(user_ids)))
    users_by_id = {user.get("id"): user.get("email") for user in users}

    formatted_trades = []
    for trade in trades:
        trading_pair = trade.get("trading_pair", "")
        symbol = trading_pair.split("/")[0] if trading_pair else None
        created_at = trade.get("created_at")
        formatted_trades.append({
            "id": trade.get("id"),
            "userId": trade.get("user_id"),
            "userEmail": users_by_id.get(trade.get("user_id")),
            "type": (trade.get("side") or "").lower(),
            "symbol": symbol,
            "amount": trade.get("amount"),
            "price": trade.get("price"),
            "status": trade.get("status", "filled"),
            "timestamp": created_at.isoformat() if hasattr(created_at, "isoformat") else None
        })
    
    return {
        "trades": formatted_trades,
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
    export: bool = False,
    admin_check: bool = Depends(is_admin),
    db = Depends(get_db)
):
    """
    Get audit logs with optional filters.

    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 1000 for export)
    - user_id: Filter by user ID
    - action: Filter by action type
    - export: If true, return as CSV file download instead of JSON
    """
    audit_collection = db.get_collection("audit_logs")

    query = {}
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action

    # For export, fetch all matching records (or up to 10000 for safety)
    if export:
        export_limit = min(limit, 10000) if limit else 10000
        logs = await audit_collection.find(query).sort("created_at", -1).to_list(export_limit)
        logs = [normalize_audit_log(log) for log in logs]

        # Generate CSV
        if not logs:
            # Return empty CSV with headers
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=["timestamp", "user_id", "action", "resource", "ip_address", "details"])
            writer.writeheader()
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
            )

        # Write CSV to string buffer
        output = StringIO()

        # Get all unique field names from logs
        fieldnames = set()
        for log in logs:
            fieldnames.update(log.keys() if isinstance(log, dict) else [])
        fieldnames = sorted(list(fieldnames))

        # Prioritize important fields first
        important_fields = ["timestamp", "user_id", "action", "resource", "ip_address", "details", "request_id"]
        ordered_fields = [f for f in important_fields if f in fieldnames]
        other_fields = [f for f in fieldnames if f not in ordered_fields]
        all_fields = ordered_fields + other_fields

        writer = csv.DictWriter(output, fieldnames=all_fields, restval="")
        writer.writeheader()

        for log in logs:
            # Convert ObjectId and datetime to strings
            cleaned_log = {}
            for field in all_fields:
                value = log.get(field, "")
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, '__dict__'):
                    value = str(value)
                cleaned_log[field] = value
            writer.writerow(cleaned_log)

        csv_content = output.getvalue()
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
        )

    # Standard JSON response
    logs = await audit_collection.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    logs = [normalize_audit_log(log) for log in logs]
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
