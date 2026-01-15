"""Admin dashboard and management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import Optional

from ..dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/admin", tags=["admin"])


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
