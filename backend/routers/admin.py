"""
Admin Dashboard API Routes
Complete admin control panel with real-time capabilities
"""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request, Response, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from database import get_database
from dependencies import db_connection
from admin_auth import (
    AdminLoginRequest, AdminLoginResponse, AdminUser,
    get_current_admin, create_admin_token, verify_password,
    hash_password, log_admin_action, ADMIN_PERMISSIONS
)
from config import settings
from socketio_server import socketio_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


def get_db():
    """Get database instance from dependencies"""
    if not db_connection or not db_connection.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )
    return db_connection.db


# ============================================
# PYDANTIC MODELS
# ============================================

class UserActionRequest(BaseModel):
    """Request to perform action on user"""
    action: str  # suspend, unsuspend, verify, delete, reset_password
    reason: Optional[str] = None
    duration_hours: Optional[int] = None  # For temporary suspensions


class WalletAdjustRequest(BaseModel):
    """Request to adjust user wallet"""
    user_id: str
    currency: str
    amount: float
    reason: str
    transaction_type: str = "admin_adjustment"


class AdminCreateRequest(BaseModel):
    """Request to create new admin"""
    email: EmailStr
    name: str
    password: str
    role: str = "admin"


class SystemConfigUpdate(BaseModel):
    """System configuration update"""
    key: str
    value: Any
    description: Optional[str] = None


class BroadcastMessage(BaseModel):
    """Broadcast message to users"""
    title: str
    message: str
    type: str = "info"  # info, warning, critical
    target: str = "all"  # all, verified, active
    expires_at: Optional[datetime] = None


# ============================================
# ADMIN AUTHENTICATION
# ============================================

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    request: Request,
    response: Response,
    credentials: AdminLoginRequest
):
    """
    Admin login with enhanced security.
    Returns JWT token and sets secure cookie.
    """
    db = get_db()
    
    # Find admin by email
    admin = await db.admins.find_one({"email": credentials.email.lower()})
    
    if not admin:
        logger.warning(f"Admin login attempt with unknown email: {credentials.email}")
        await log_admin_action(
            admin_id="unknown",
            action="login_failed",
            resource_type="admin",
            resource_id="unknown",
            details={"email": credentials.email, "reason": "unknown_email"},
            ip_address=request.client.host
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(credentials.password, admin["password_hash"]):
        logger.warning(f"Admin login failed for: {credentials.email}")
        await log_admin_action(
            admin_id=admin["id"],
            action="login_failed",
            resource_type="admin",
            resource_id=admin["id"],
            details={"reason": "invalid_password"},
            ip_address=request.client.host
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if account is active
    if not admin.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is deactivated"
        )
    
    # Check 2FA if enabled
    if admin.get("two_factor_enabled"):
        if not credentials.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA code required"
            )
    
    # Create token
    token, expires_at = create_admin_token(
        admin["id"],
        admin["email"],
        admin["role"]
    )
    
    # Update last login
    await db.admins.update_one(
        {"id": admin["id"]},
        {
            "$set": {"last_login": datetime.now(timezone.utc)},
            "$push": {
                "login_history": {
                    "$each": [{
                        "timestamp": datetime.now(timezone.utc),
                        "ip_address": request.client.host,
                        "user_agent": request.headers.get("user-agent", "unknown")
                    }],
                    "$slice": -20
                }
            }
        }
    )
    
    # Log successful login
    await log_admin_action(
        admin_id=admin["id"],
        action="login_success",
        resource_type="admin",
        resource_id=admin["id"],
        details={"user_agent": request.headers.get("user-agent", "unknown")},
        ip_address=request.client.host
    )
    
    # Set secure cookie
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        secure=settings.use_cross_site_cookies,
        samesite="lax" if not settings.use_cross_site_cookies else "none",
        max_age=8 * 60 * 60,
        path="/api/admin"
    )
    
    logger.info(f"Admin login successful: {admin['email']}")
    
    return {
        "admin": {
            "id": admin["id"],
            "email": admin["email"],
            "name": admin["name"],
            "role": admin["role"],
            "permissions": admin.get("permissions", ADMIN_PERMISSIONS.get(admin["role"], []))
        },
        "token": token,
        "expires_at": expires_at
    }


@router.post("/logout")
async def admin_logout(
    response: Response,
    current_admin: dict = Depends(get_current_admin)
):
    """Admin logout - clear session"""
    response.delete_cookie("admin_token", path="/api/admin")
    
    await log_admin_action(
        admin_id=current_admin["id"],
        action="logout",
        resource_type="admin",
        resource_id=current_admin["id"],
        details={},
        ip_address=None
    )
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_admin_profile(current_admin: dict = Depends(get_current_admin)):
    """Get current admin profile"""
    return {"admin": current_admin}


# ============================================
# DASHBOARD OVERVIEW
# ============================================

@router.get("/dashboard/stats")
async def get_dashboard_stats(current_admin: dict = Depends(get_current_admin)):
    """Get real-time dashboard statistics."""
    db = get_db()
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    # User statistics
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    verified_users = await db.users.count_documents({"email_verified": True})
    suspended_users = await db.users.count_documents({"is_suspended": True})
    new_users_today = await db.users.count_documents({"created_at": {"$gte": today_start}})
    new_users_week = await db.users.count_documents({"created_at": {"$gte": week_start}})
    
    # Transaction statistics
    total_transactions = await db.transactions.count_documents({})
    transactions_today = await db.transactions.count_documents({"created_at": {"$gte": today_start}})
    
    # Volume calculation
    pipeline = [
        {"$match": {"created_at": {"$gte": today_start}, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    volume_result = await db.transactions.aggregate(pipeline).to_list(1)
    volume_today = volume_result[0]["total"] if volume_result else 0
    
    # Pending items
    pending_withdrawals = await db.withdrawals.count_documents({"status": "pending"})
    pending_deposits = await db.deposits.count_documents({"status": "pending"})
    
    # Active sessions
    active_connections = socketio_manager.get_stats().get("active_connections", 0)
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "suspended": suspended_users,
            "new_today": new_users_today,
            "new_week": new_users_week,
            "growth_rate": round((new_users_week / max(total_users - new_users_week, 1)) * 100, 2)
        },
        "transactions": {
            "total": total_transactions,
            "today": transactions_today,
            "volume_today": round(volume_today, 2)
        },
        "pending": {
            "withdrawals": pending_withdrawals,
            "deposits": pending_deposits,
            "total": pending_withdrawals + pending_deposits
        },
        "system": {
            "active_connections": active_connections,
            "server_time": now.isoformat(),
            "environment": settings.environment
        }
    }


@router.get("/dashboard/charts")
async def get_dashboard_charts(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    current_admin: dict = Depends(get_current_admin)
):
    """Get chart data for dashboard visualizations"""
    db = get_db()
    now = datetime.now(timezone.utc)
    
    if period == "day":
        start_date = now - timedelta(days=1)
        group_format = "%Y-%m-%d %H:00"
    elif period == "week":
        start_date = now - timedelta(weeks=1)
        group_format = "%Y-%m-%d"
    elif period == "month":
        start_date = now - timedelta(days=30)
        group_format = "%Y-%m-%d"
    else:
        start_date = now - timedelta(days=365)
        group_format = "%Y-%m"
    
    # User registrations over time
    user_pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": group_format, "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    user_data = await db.users.aggregate(user_pipeline).to_list(100)
    
    # Transaction volume over time
    tx_pipeline = [
        {"$match": {"created_at": {"$gte": start_date}, "status": "completed"}},
        {"$group": {
            "_id": {"$dateToString": {"format": group_format, "date": "$created_at"}},
            "volume": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    tx_data = await db.transactions.aggregate(tx_pipeline).to_list(100)
    
    return {
        "period": period,
        "user_registrations": [{"date": d["_id"], "count": d["count"]} for d in user_data],
        "transaction_volume": [{"date": d["_id"], "volume": d["volume"], "count": d["count"]} for d in tx_data]
    }


# ============================================
# USER MANAGEMENT
# ============================================

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_admin: dict = Depends(get_current_admin)
):
    """List all users with filtering and pagination."""
    db = get_db()
    
    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"id": search}
        ]
    if status:
        if status == "active":
            query["is_active"] = True
            query["is_suspended"] = {"$ne": True}
        elif status == "suspended":
            query["is_suspended"] = True
        elif status == "verified":
            query["email_verified"] = True
        elif status == "unverified":
            query["email_verified"] = {"$ne": True}
    
    sort_direction = -1 if sort_order == "desc" else 1
    
    cursor = db.users.find(
        query,
        {"password_hash": 0, "two_factor_secret": 0, "email_verification_token": 0, "password_reset_token": 0}
    ).sort(sort_by, sort_direction).skip(skip).limit(limit)
    
    users = await cursor.to_list(limit)
    total = await db.users.count_documents(query)
    
    enriched_users = []
    for user in users:
        wallet = await db.wallets.find_one({"user_id": user["id"]})
        enriched_users.append({
            **user,
            "_id": str(user.get("_id", "")),
            "wallet_balance": wallet.get("balances", {}) if wallet else {},
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
            "last_login": user.get("last_activity").isoformat() if user.get("last_activity") else None
        })
    
    return {"users": enriched_users, "total": total, "skip": skip, "limit": limit}


@router.get("/users/{user_id}")
async def get_user_detail(user_id: str, current_admin: dict = Depends(get_current_admin)):
    """Get detailed user information"""
    db = get_db()
    
    user = await db.users.find_one({"id": user_id}, {"password_hash": 0, "two_factor_secret": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    wallet = await db.wallets.find_one({"user_id": user_id})
    transactions = await db.transactions.find({"user_id": user_id}).sort("created_at", -1).limit(20).to_list(20)
    
    return {
        "user": {**user, "_id": str(user.get("_id", "")), "created_at": user.get("created_at").isoformat() if user.get("created_at") else None},
        "wallet": wallet,
        "recent_transactions": transactions
    }


@router.post("/users/{user_id}/action")
async def perform_user_action(
    request: Request,
    user_id: str,
    action_request: UserActionRequest,
    current_admin: dict = Depends(get_current_admin)
):
    """Perform administrative action on a user."""
    db = get_db()
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    action = action_request.action
    updates = {}
    notification_message = None
    
    if action == "suspend":
        updates["is_suspended"] = True
        updates["suspended_at"] = datetime.now(timezone.utc)
        updates["suspended_reason"] = action_request.reason
        updates["suspended_by"] = current_admin["id"]
        if action_request.duration_hours:
            updates["suspension_expires"] = datetime.now(timezone.utc) + timedelta(hours=action_request.duration_hours)
        notification_message = f"Your account has been suspended. Reason: {action_request.reason or 'Policy violation'}"
        
    elif action == "unsuspend":
        updates["is_suspended"] = False
        updates["suspended_at"] = None
        updates["suspended_reason"] = None
        notification_message = "Your account suspension has been lifted."
        
    elif action == "verify":
        updates["email_verified"] = True
        updates["email_verified_at"] = datetime.now(timezone.utc)
        notification_message = "Your email has been verified by an administrator."
        
    elif action == "delete":
        updates["is_active"] = False
        updates["deleted_at"] = datetime.now(timezone.utc)
        updates["deleted_by"] = current_admin["id"]
        
    elif action == "force_logout":
        await db.sessions.delete_many({"user_id": user_id})
        notification_message = "You have been logged out of all sessions."
        
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    if updates:
        await db.users.update_one({"id": user_id}, {"$set": updates})
    
    if notification_message:
        await db.notifications.insert_one({
            "id": secrets.token_hex(16),
            "user_id": user_id,
            "type": "admin_action",
            "title": f"Account {action}",
            "message": notification_message,
            "read": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        await socketio_manager.send_to_user(user_id, "notification", {
            "type": "admin_action",
            "action": action,
            "message": notification_message
        })
    
    await log_admin_action(
        admin_id=current_admin["id"],
        action=f"user_{action}",
        resource_type="user",
        resource_id=user_id,
        details={"reason": action_request.reason, "user_email": user.get("email")},
        ip_address=request.client.host
    )
    
    return {"message": f"Action '{action}' performed successfully", "user_id": user_id, "action": action}


# ============================================
# WALLET MANAGEMENT
# ============================================

@router.post("/wallets/adjust")
async def adjust_wallet(
    request: Request,
    adjustment: WalletAdjustRequest,
    current_admin: dict = Depends(get_current_admin)
):
    """Manually adjust user wallet balance."""
    db = get_db()
    
    user = await db.users.find_one({"id": adjustment.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    wallet = await db.wallets.find_one({"user_id": adjustment.user_id})
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    current_balance = wallet.get("balances", {}).get(adjustment.currency, 0)
    new_balance = current_balance + adjustment.amount
    
    if new_balance < 0:
        raise HTTPException(status_code=400, detail=f"Adjustment would result in negative balance")
    
    await db.wallets.update_one(
        {"user_id": adjustment.user_id},
        {"$set": {f"balances.{adjustment.currency}": new_balance}}
    )
    
    tx_id = secrets.token_hex(16)
    await db.transactions.insert_one({
        "id": tx_id,
        "user_id": adjustment.user_id,
        "type": adjustment.transaction_type,
        "amount": adjustment.amount,
        "currency": adjustment.currency,
        "status": "completed",
        "description": f"Admin adjustment: {adjustment.reason}",
        "metadata": {
            "admin_id": current_admin["id"],
            "reason": adjustment.reason,
            "previous_balance": current_balance,
            "new_balance": new_balance
        },
        "created_at": datetime.now(timezone.utc)
    })
    
    await log_admin_action(
        admin_id=current_admin["id"],
        action="wallet_adjustment",
        resource_type="wallet",
        resource_id=adjustment.user_id,
        details={"currency": adjustment.currency, "amount": adjustment.amount, "reason": adjustment.reason},
        ip_address=request.client.host
    )
    
    await socketio_manager.send_to_user(adjustment.user_id, "wallet_update", {
        "currency": adjustment.currency,
        "balance": new_balance,
        "change": adjustment.amount
    })
    
    return {"message": "Wallet adjusted successfully", "transaction_id": tx_id, "previous_balance": current_balance, "new_balance": new_balance}


# ============================================
# TRANSACTIONS MANAGEMENT
# ============================================

@router.get("/transactions")
async def list_all_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """List all transactions with filtering"""
    db = get_db()
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if type:
        query["type"] = type
    if status:
        query["status"] = status
    
    cursor = db.transactions.find(query).sort("created_at", -1).skip(skip).limit(limit)
    transactions = await cursor.to_list(limit)
    total = await db.transactions.count_documents(query)
    
    return {"transactions": transactions, "total": total, "skip": skip, "limit": limit}


# ============================================
# SYSTEM MANAGEMENT
# ============================================

@router.get("/system/health")
async def get_system_health(current_admin: dict = Depends(get_current_admin)):
    """Get comprehensive system health status"""
    db = get_db()
    
    health = {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "services": {}}
    
    try:
        await db.command("ping")
        health["services"]["mongodb"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["mongodb"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    try:
        from redis_cache import redis_cache
        is_connected = await redis_cache.is_connected()
        health["services"]["redis"] = {"status": "healthy" if is_connected else "disconnected"}
    except:
        health["services"]["redis"] = {"status": "error"}
    
    stats = socketio_manager.get_stats()
    health["services"]["socketio"] = {"status": "healthy", "active_connections": stats.get("active_connections", 0)}
    
    return health


@router.post("/system/broadcast")
async def broadcast_message(message: BroadcastMessage, current_admin: dict = Depends(get_current_admin)):
    """Broadcast message to all connected users"""
    await socketio_manager.broadcast("announcement", {
        "title": message.title,
        "message": message.message,
        "type": message.type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"message": "Broadcast sent successfully"}


# ============================================
# AUDIT LOGS
# ============================================

@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin_id: Optional[str] = None,
    action: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """Get admin audit logs"""
    db = get_db()
    
    query = {}
    if admin_id:
        query["admin_id"] = admin_id
    if action:
        query["action"] = action
    
    cursor = db.admin_audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(limit)
    total = await db.admin_audit_logs.count_documents(query)
    
    return {"logs": logs, "total": total, "skip": skip, "limit": limit}


# ============================================
# ADMIN MANAGEMENT
# ============================================

@router.get("/admins")
async def list_admins(current_admin: dict = Depends(get_current_admin)):
    """List all admin accounts"""
    if current_admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    db = get_db()
    admins = await db.admins.find({}, {"password_hash": 0, "two_factor_secret": 0}).to_list(100)
    return {"admins": admins}


@router.post("/admins")
async def create_admin(
    request: Request,
    admin_data: AdminCreateRequest,
    current_admin: dict = Depends(get_current_admin)
):
    """Create new admin account"""
    if current_admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    db = get_db()
    
    existing = await db.admins.find_one({"email": admin_data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    admin_id = secrets.token_hex(16)
    
    await db.admins.insert_one({
        "id": admin_id,
        "email": admin_data.email.lower(),
        "password_hash": hash_password(admin_data.password),
        "name": admin_data.name,
        "role": admin_data.role,
        "permissions": ADMIN_PERMISSIONS.get(admin_data.role, []),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "created_by": current_admin["id"]
    })
    
    await log_admin_action(
        admin_id=current_admin["id"],
        action="admin_create",
        resource_type="admin",
        resource_id=admin_id,
        details={"email": admin_data.email, "role": admin_data.role},
        ip_address=request.client.host
    )
    
    return {"message": "Admin created successfully", "admin_id": admin_id}
