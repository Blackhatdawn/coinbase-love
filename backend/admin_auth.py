"""
Admin Authentication and Authorization System
Enterprise-grade admin control panel security
"""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps

from fastapi import HTTPException, Request, Depends, status
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr

from config import settings
from database import get_database

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Admin JWT settings (separate from user JWT)
ADMIN_SECRET_KEY = settings.jwt_secret.get_secret_value() + "_admin_panel"
ADMIN_TOKEN_EXPIRE_HOURS = 8  # Admin sessions expire faster


class AdminUser(BaseModel):
    """Admin user model"""
    id: str
    email: EmailStr
    name: str
    role: str = "admin"  # admin, super_admin
    permissions: List[str] = []
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    

class AdminLoginRequest(BaseModel):
    """Admin login request"""
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class AdminLoginResponse(BaseModel):
    """Admin login response"""
    admin: Dict[str, Any]
    token: str
    expires_at: datetime


# Default admin permissions
ADMIN_PERMISSIONS = {
    "super_admin": [
        "users:read", "users:write", "users:delete", "users:suspend",
        "wallets:read", "wallets:write", "wallets:adjust",
        "transactions:read", "transactions:void", "transactions:refund",
        "system:read", "system:write", "system:config",
        "admins:read", "admins:write", "admins:delete",
        "audit:read", "audit:export",
        "reports:read", "reports:export"
    ],
    "admin": [
        "users:read", "users:write", "users:suspend",
        "wallets:read", "wallets:adjust",
        "transactions:read", "transactions:void",
        "system:read",
        "audit:read",
        "reports:read"
    ],
    "moderator": [
        "users:read", "users:suspend",
        "wallets:read",
        "transactions:read",
        "audit:read"
    ]
}


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_admin_token(admin_id: str, email: str, role: str) -> tuple[str, datetime]:
    """Create an admin JWT token"""
    expires = datetime.now(timezone.utc) + timedelta(hours=ADMIN_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": admin_id,
        "email": email,
        "role": role,
        "type": "admin",
        "exp": expires,
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, ADMIN_SECRET_KEY, algorithm=settings.jwt_algorithm)
    return token, expires


def decode_admin_token(token: str) -> Optional[Dict]:
    """Decode and verify an admin JWT token"""
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "admin":
            return None
        return payload
    except JWTError as e:
        logger.warning(f"Admin token decode error: {e}")
        return None


async def get_current_admin(request: Request) -> Dict:
    """
    Dependency to get the current authenticated admin.
    Checks both cookie and Authorization header.
    """
    # Try cookie first
    token = request.cookies.get("admin_token")
    
    # Then try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required"
        )
    
    payload = decode_admin_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token"
        )
    
    # Verify admin still exists and is active
    from dependencies import db_connection
    if not db_connection or not db_connection.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )
    
    db = db_connection.db
    admin = await db.admins.find_one({"id": payload["sub"], "is_active": True})
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account not found or deactivated"
        )
    
    return {
        "id": admin["id"],
        "email": admin["email"],
        "name": admin["name"],
        "role": admin["role"],
        "permissions": admin.get("permissions", ADMIN_PERMISSIONS.get(admin["role"], []))
    }


def require_permission(permission: str):
    """Decorator to require a specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get admin from kwargs (injected by Depends)
            admin = kwargs.get("current_admin")
            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Admin authentication required"
                )
            
            permissions = admin.get("permissions", [])
            if permission not in permissions and admin.get("role") != "super_admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def create_default_admin():
    """Create default super admin if none exists"""
    from dependencies import db_connection
    
    if not db_connection or not db_connection.is_connected:
        logger.warning("Database not connected, skipping admin initialization")
        return
    
    db = db_connection.db
    
    # Check if any admin exists
    existing = await db.admins.find_one({})
    if existing:
        logger.info("✅ Admin account already exists")
        return
    
    # Create default super admin
    admin_id = secrets.token_hex(16)
    default_password = "CryptoVault@Admin2026!"  # Should be changed immediately
    
    admin_doc = {
        "id": admin_id,
        "email": "admin@cryptovault.financial",
        "password_hash": hash_password(default_password),
        "name": "Super Admin",
        "role": "super_admin",
        "permissions": ADMIN_PERMISSIONS["super_admin"],
        "is_active": True,
        "require_password_change": True,
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
        "login_history": [],
        "two_factor_enabled": False,
        "two_factor_secret": None
    }
    
    await db.admins.insert_one(admin_doc)
    logger.info("=" * 60)
    logger.info("🔐 DEFAULT ADMIN ACCOUNT CREATED")
    logger.info(f"   Email: admin@cryptovault.financial")
    logger.info(f"   Password: {default_password}")
    logger.info("   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
    logger.info("=" * 60)


async def log_admin_action(
    admin_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Dict[str, Any],
    ip_address: str = None
):
    """Log admin actions for audit trail"""
    db = await get_database()
    
    log_entry = {
        "id": secrets.token_hex(16),
        "admin_id": admin_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
        "ip_address": ip_address,
        "timestamp": datetime.now(timezone.utc),
        "type": "admin_action"
    }
    
    await db.admin_audit_logs.insert_one(log_entry)
    logger.info(f"Admin action logged: {action} on {resource_type}/{resource_id}")
