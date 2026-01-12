"""
Production-ready FastAPI server with updated MongoDB connection management (health checks, exponential backoff,
timeouts, validation), real-time price integration in portfolio, proper root endpoint, secure logout
with token blacklisting, CSRF token endpoint, and all recovered endpoints properly aligned.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, status, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import List, Optional, Set, Dict, Any
from datetime import datetime, timedelta
from config import settings
import asyncio
import json
import os
import uuid  # For CSRF token

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Import configuration
from config import settings

# Import models
from models import (
    User, UserCreate, UserLogin, UserResponse,
    Cryptocurrency, Portfolio, Holding, HoldingCreate,
    Order, OrderCreate, Transaction, TransactionCreate,
    AuditLog, TwoFactorSetup, TwoFactorVerify, BackupCodes,
    VerifyEmailRequest, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)

from email_service import (
    email_service,
    generate_verification_code,
    generate_verification_token,
    generate_password_reset_token,
    get_token_expiration
)

from auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, generate_backup_codes, generate_2fa_secret
)

from dependencies import get_current_user_id, optional_current_user_id
from coingecko_service import coingecko_service
from security_middleware import SecurityMiddleware, CSRFMiddleware

# Blacklist import for secure logout
from blacklist import blacklist_token

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# DATABASE CONNECTION (production-ready)
# ============================================

class DatabaseConnection:
    """Manages MongoDB connection with health checks, retries, and graceful cleanup."""

    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        max_pool_size: int = 50,
        min_pool_size: int = 10,
        server_selection_timeout_ms: int = 5000,
        base_retry_delay: float = 2.0,
        client_options: Optional[Dict[str, Any]] = None,
    ):
        if not mongo_url:
            raise ValueError("mongo_url is required")
        if not db_name or not db_name.strip():
            raise ValueError("db_name is required and cannot be empty")

        if not (mongo_url.startswith("mongodb://") or mongo_url.startswith("mongodb+srv://")):
            raise ValueError("mongo_url must start with mongodb:// or mongodb+srv://")

        self.mongo_url = mongo_url
        self.db_name = db_name.strip()
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.server_selection_timeout_ms = server_selection_timeout_ms
        self.base_retry_delay = base_retry_delay
        self.client_options = client_options or {}

        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False

    def _cleanup(self):
        """Internal cleanup of client state."""
        self.client = None
        self.db = None
        self._is_connected = False

    async def connect(
        self,
        max_retries: int = 5,
        base_retry_delay: Optional[float] = None,
    ):
        base_retry_delay = base_retry_delay or self.base_retry_delay

        if self.client:
            try:
                await asyncio.wait_for(self.client.admin.command("ping"), timeout=5.0)
                if self._is_connected:
                    logger.info("✅ MongoDB connection is already healthy.")
                    return
            except Exception as e:
                logger.warning(f"⚠️ Existing connection unhealthy ({str(e)}). Reconnecting...")
                await self.disconnect()

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔌 Attempting MongoDB connection (attempt {attempt}/{max_retries})...")

                self.client = AsyncIOMotorClient(
                    self.mongo_url,
                    maxPoolSize=self.max_pool_size,
                    minPoolSize=self.min_pool_size,
                    serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                    retryWrites=True,
                    retryReads=True,
                    **self.client_options,
                )

                self.db = self.client[self.db_name]

                await asyncio.wait_for(self.health_check(), timeout=10.0)

                self._is_connected = True
                logger.info(f"✅ MongoDB connected successfully to database: {self.db_name}")
                logger.debug(f"Pool size: {self.min_pool_size}-{self.max_pool_size}")
                logger.debug(f"Server selection timeout: {self.server_selection_timeout_ms}ms")
                return

            except (ConnectionFailure, ServerSelectionTimeoutError, asyncio.TimeoutError) as e:
                logger.error(f"❌ Connection failed (attempt {attempt}/{max_retries}): {str(e)}")
                self._cleanup()

                if attempt < max_retries:
                    delay = base_retry_delay * (2 ** (attempt - 1))
                    logger.info(f"⏳ Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.critical("💥 Failed to connect to MongoDB after all retries")
                    raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")

            except Exception as e:
                logger.critical(f"💥 Unexpected error during connection: {str(e)}")
                self._cleanup()
                raise

    async def health_check(self) -> bool:
        """Perform a ping health check on the MongoDB server."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        try:
            await self.client.admin.command("ping")
            logger.debug("✅ MongoDB health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB health check failed: {str(e)}")
            self._is_connected = False
            raise

    async def disconnect(self):
        """Gracefully close the database connection."""
        if self.client:
            logger.info("🔌 Closing MongoDB connection...")
            self.client.close()
            self._cleanup()
            logger.info("✅ MongoDB connection closed")

    @property
    def is_connected(self) -> bool:
        """Quick flag-based check if the database appears connected."""
        return self._is_connected and self.client is not None and self.db is not None

    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if not self.db or not self.is_connected:
            raise RuntimeError("Database not connected.")
        return self.db[collection_name]

# Global database connection instance
db_connection: Optional[DatabaseConnection] = None

# ============================================
# CREATE FASTAPI APP
# ============================================

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="CryptoVault API",
    version="1.0.0",
    description="Production-ready cryptocurrency trading platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_router = APIRouter(prefix="/api")

# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint – friendly welcome for crawlers, health checks, and users."""
    return {
        "message": "🚀 CryptoVault API is live and running!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# CSRF TOKEN ENDPOINT
# ============================================

@app.get("/csrf", tags=["auth"])
async def get_csrf_token(request: Request):
    """Get or set CSRF token (frontend can fetch on load)."""
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = str(uuid.uuid4())
        response = JSONResponse({"csrf_token": csrf_token})
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=True,
            secure=(settings.environment == "production"),
            samesite="lax",
            max_age=3600
        )
        return response
    return {"csrf_token": csrf_token}

# ============================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    global db_connection
    logger.info("="*70)
    logger.info("🚀 Starting CryptoVault API Server")
    logger.info("="*70)

    try:
        db_connection = DatabaseConnection(
            mongo_url=settings.mongo_url,
            db_name=settings.db_name
        )
        await db_connection.connect()

        # Ensure TTL index for blacklisted_tokens (Mongo fallback)
        try:
            if db_connection and db_connection.is_connected:
                collection = db_connection.get_collection("blacklisted_tokens")
                await collection.create_index("expires_at", expireAfterSeconds=0)
                logger.info("✅ Ensured TTL index on blacklisted_tokens.expires_at")
            else:
                logger.debug("DB not connected yet – skipping TTL index creation")
        except Exception as e:
            logger.warning(f"⚠️ TTL index creation failed (non-critical): {str(e)}")

        logger.info("="*70)
        logger.info("✅ Server startup complete!")
        logger.info(f" Environment: {settings.environment}")
        logger.info(f" Database: {settings.db_name}")
        logger.info(f" JWT Secret: ***[{len(settings.jwt_secret)} chars]***")
        logger.info(f" Rate Limit: {settings.rate_limit_per_minute} req/min")
        logger.info("="*70)

    except Exception as e:
        logger.critical(f"💥 Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global db_connection
    logger.info("="*70)
    logger.info("🛑 Shutting down CryptoVault API Server")
    logger.info("="*70)

    if db_connection:
        await db_connection.disconnect()
    logger.info("✅ Graceful shutdown complete")

# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get("/health", tags=["health"])
async def health_check():
    global db_connection
    try:
        if not db_connection or not await db_connection.health_check():
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.environment,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# ============================================
# HELPER FUNCTIONS
# ============================================

async def log_audit(user_id: str, action: str, resource: Optional[str] = None,
                   ip_address: Optional[str] = None, details: Optional[dict] = None):
    global db_connection
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        details=details
    )
    await db_connection.get_collection("audit_logs").insert_one(audit_log.dict())

# ============================================
# AUTH ENDPOINTS (recovered and aligned)
# ============================================

@api_router.post("/auth/signup", tags=["auth"])
@limiter.limit("5/minute")
async def signup(user_data: UserCreate, request: Request):
    """Register a new user with email verification"""
    users_collection = db_connection.get_collection("users")
    portfolios_collection = db_connection.get_collection("portfolios")

    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    verification_code = generate_verification_code()
    verification_token = generate_verification_token()
    verification_expires = get_token_expiration(hours=24)

    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        email_verified=False,
        email_verification_code=verification_code,
        email_verification_token=verification_token,
        email_verification_expires=verification_expires
    )

    await users_collection.insert_one(user.dict())

    portfolio = Portfolio(user_id=user.id)
    await portfolios_collection.insert_one(portfolio.dict())

    app_url = settings.app_url  # From settings (better than os.environ)
    subject, html_content, text_content = email_service.get_verification_email(
        name=user.name,
        code=verification_code,
        token=verification_token,
        app_url=app_url
    )

    email_sent = await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    if not email_sent:
        logger.warning(f"⚠️ Verification email failed to send to {user.email}")

    await log_audit(user.id, "USER_SIGNUP", ip_address=request.client.host)

    return {
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict(),
        "message": "Account created! Please check your email to verify your account.",
        "emailSent": email_sent,
        "verificationRequired": True
    }

@api_router.post("/auth/login", tags=["auth"])
@limiter.limit("10/minute")
async def login(credentials: UserLogin, request: Request):
    """Login user with account lockout protection"""
    users_collection = db_connection.get_collection("users")

    user_doc = await users_collection.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = User(**user_doc)

    if user.locked_until and user.locked_until > datetime.utcnow():
        minutes_left = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=429,
            detail=f"Account locked due to too many failed attempts. Try again in {minutes_left} minutes."
        )

    if not verify_password(credentials.password, user.password_hash):
        failed_attempts = user.failed_login_attempts + 1
        update_data = {"failed_login_attempts": failed_attempts}
        if failed_attempts >= 5:
            update_data["locked_until"] = datetime.utcnow() + timedelta(minutes=15)
            await users_collection.update_one({"id": user.id}, {"$set": update_data})
            await log_audit(user.id, "ACCOUNT_LOCKED", ip_address=request.client.host)
            raise HTTPException(
                status_code=429,
                detail="Account locked for 15 minutes due to too many failed login attempts."
            )
        await users_collection.update_one({"id": user.id}, {"$set": update_data})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.email_verified:
        raise HTTPException(
            status_code=401,
            detail="Email not verified. Please check your email and verify your account."
        )

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login": datetime.utcnow()
        }}
    )

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    await log_audit(user.id, "USER_LOGIN", ip_address=request.client.host)

    response = JSONResponse(content={
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    })
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.environment == 'production',
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment == 'production',
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )
    return response

@api_router.post("/auth/logout", tags=["auth"])
async def logout(request: Request, user_id: str = Depends(get_current_user_id)):
    """Secure logout: Blacklist tokens and delete cookies."""
    refresh_token = request.cookies.get("refresh_token")
    access_token = request.cookies.get("access_token")

    if refresh_token:
        payload = decode_token(refresh_token)
        if payload and payload.get("type") == "refresh":
            expires_in = int(payload["exp"] - datetime.utcnow().timestamp())
            await blacklist_token(refresh_token, max(expires_in, 60))

    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("type") == "access":
            expires_in = int(payload["exp"] - datetime.utcnow().timestamp())
            await blacklist_token(access_token, max(expires_in, 60))

    await log_audit(user_id, "USER_LOGOUT", ip_address=request.client.host)

    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@api_router.get("/auth/me", tags=["auth"])
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """Get current user profile"""
    users_collection = db_connection.get_collection("users")
    user_doc = await users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    user = User(**user_doc)
    return {
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    }

@api_router.post("/auth/refresh", tags=["auth"])
async def refresh_token(request: Request):
    """Refresh access token"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    access_token = create_access_token(data={"sub": user_id})

    response = JSONResponse(content={"message": "Token refreshed"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.environment == 'production',
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60
    )

    return response

@api_router.post("/auth/verify-email", tags=["auth"])
@limiter.limit("10/minute")
async def verify_email(data: VerifyEmailRequest, request: Request):
    """Verify email with code or token"""
    users_collection = db_connection.get_collection("users")

    user_doc = await users_collection.find_one({
        "": [
            {"email_verification_code": data.token},
            {"email_verification_token": data.token}
        ]
    })

    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user = User(**user_doc)

    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    if user.email_verification_expires < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Verification code expired. Please request a new one."
        )

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "email_verified": True,
            "email_verification_code": None,
            "email_verification_token": None,
            "email_verification_expires": None
        }}
    )

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    await log_audit(user.id, "EMAIL_VERIFIED")

    subject, html_content, text_content = email_service.get_welcome_email(
        name=user.name,
        app_url=settings.app_url
    )
    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    response = JSONResponse(content={
        "message": "Email verified successfully!",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    })

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.environment == 'production',
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment == 'production',
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )

    return response

@api_router.post("/auth/resend-verification", tags=["auth"])
@limiter.limit("3/minute")
async def resend_verification(data: ResendVerificationRequest, request: Request):
    """Resend verification email"""
    users_collection = db_connection.get_collection("users")

    user_doc = await users_collection.find_one({"email": data.email})
    if not user_doc:
        return {"message": "If this email is registered, a verification email has been sent."}

    user = User(**user_doc)

    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    verification_code = generate_verification_code()
    verification_token = generate_verification_token()
    verification_expires = get_token_expiration(hours=24)

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "email_verification_code": verification_code,
            "email_verification_token": verification_token,
            "email_verification_expires": verification_expires
        }}
    )

    subject, html_content, text_content = email_service.get_verification_email(
        name=user.name,
        code=verification_code,
        token=verification_token,
        app_url=settings.app_url
    )

    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    return {"message": "Verification email sent! Please check your inbox."}

@api_router.post("/auth/forgot-password", tags=["auth"])
@limiter.limit("3/minute")
async def forgot_password(data: ForgotPasswordRequest, request: Request):
    """Request password reset email"""
    users_collection = db_connection.get_collection("users")

    user_doc = await users_collection.find_one({"email": data.email})

    if not user_doc:
        return {"message": "If this email is registered, a password reset link has been sent."}

    user = User(**user_doc)

    reset_token = generate_password_reset_token()
    reset_expires = get_token_expiration(hours=1)

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "password_reset_token": reset_token,
            "password_reset_expires": reset_expires
        }}
    )

    reset_link = f"{settings.app_url}/reset-password?token={reset_token}"

    subject, html_content, text_content = email_service.get_password_reset_email(
        name=user.name,
        reset_link=reset_link
    )

    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    await log_audit(user.id, "PASSWORD_RESET_REQUESTED")

    return {"message": "If this email is registered, a password reset link has been sent."}

@api_router.get("/auth/validate-reset-token/{token}", tags=["auth"])
async def validate_reset_token(token: str):
    """Validate if password reset token is valid"""
    users_collection = db_connection.get_collection("users")

    user_doc = await users_collection.find_one({"password_reset_token": token})

    if not user_doc:
        return {"valid": False, "message": "Invalid reset token"}

    user = User(**user_doc)

    if user.password_reset_expires < datetime.utcnow():
        return {"valid": False, "message": "Reset token expired"}

    return {"valid": True, "message": "Token is valid"}

@api_router.post("/auth/reset-password", tags=["auth"])
@limiter.limit("5/minute")
async def reset_password(data: ResetPasswordRequest, request: Request):
    """Reset password with valid token"""
    users_collection = db_connection.get_collection("users")

    user_doc = await users_collection.find_one({"password_reset_token": data.token})

    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = User(**user_doc)

    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired. Please request a new one.")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    new_password_hash = get_password_hash(data.new_password)

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "password_hash": new_password_hash,
            "password_reset_token": None,
            "password_reset_expires": None,
            "failed_login_attempts": 0,
            "locked_until": None
        }}
    )

    await log_audit(user.id, "PASSWORD_RESET_COMPLETED")

    return {"message": "Password reset successfully! You can now log in with your new password."}

# ============================================
# 2FA ENDPOINTS
# ============================================

@api_router.post("/auth/2fa/setup", tags=["auth"])
async def setup_2fa(user_id: str = Depends(get_current_user_id)):
    users_collection = db_connection.get_collection("users")
    secret = generate_2fa_secret()

    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"two_factor_secret": secret}}
    )

    return {
        "secret": secret,
        "qr_code_url": f"otpauth://totp/CryptoVault:{user_id}?secret={secret}&issuer=CryptoVault"
    }

@api_router.post("/auth/2fa/verify", tags=["auth"])
async def verify_2fa(data: TwoFactorVerify, user_id: str = Depends(get_current_user_id)):
    users_collection = db_connection.get_collection("users")

    if len(data.code) != 6 or not data.code.isdigit():
        raise HTTPException(status_code=400, detail="Invalid code")

    backup_codes = generate_backup_codes()
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {
            "two_factor_enabled": True,
            "backup_codes": backup_codes
        }}
    )

    return {
        "message": "2FA enabled successfully",
        "backup_codes": backup_codes
    }

@api_router.get("/auth/2fa/status", tags=["auth"])
async def get_2fa_status(user_id: str = Depends(get_current_user_id)):
    users_collection = db_connection.get_collection("users")
    user_doc = await users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    return {"enabled": user_doc.get("two_factor_enabled", False)}

@api_router.post("/auth/2fa/disable", tags=["auth"])
async def disable_2fa(data: dict, user_id: str = Depends(get_current_user_id)):
    users_collection = db_connection.get_collection("users")
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {
            "two_factor_enabled": False,
            "two_factor_secret": None,
            "backup_codes": []
        }}
    )

    return {"message": "2FA disabled successfully"}

@api_router.post("/auth/2fa/backup-codes", tags=["auth"])
async def get_backup_codes(user_id: str = Depends(get_current_user_id)):
    users_collection = db_connection.get_collection("users")
    backup_codes = generate_backup_codes()
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"backup_codes": backup_codes}}
    )

    return {"codes": backup_codes}

# ============================================
# CRYPTOCURRENCY ENDPOINTS
# ============================================

@api_router.get("/crypto", tags=["crypto"])
async def get_all_cryptocurrencies():
    try:
        prices = await coingecko_service.get_prices()
        return {"cryptocurrencies": prices}
    except Exception as e:
        logger.error(f"❌ Error fetching cryptocurrencies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch cryptocurrency prices")

@api_router.get("/crypto/{coin_id}", tags=["crypto"])
async def get_cryptocurrency(coin_id: str):
    try:
        coin_data = await coingecko_service.get_coin_details(coin_id.lower())
        if not coin_data:
            raise HTTPException(status_code=404, detail="Cryptocurrency not found")
        return {"cryptocurrency": coin_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching {coin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch cryptocurrency details")

@api_router.get("/crypto/{coin_id}/history", tags=["crypto"])
async def get_price_history(coin_id: str, days: int = 7):
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        history = await coingecko_service.get_price_history(coin_id.lower(), days)
        return {"coin_id": coin_id, "days": days, "history": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching history for {coin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch price history")

# ============================================
# WEBSOCKET FOR LIVE PRICE UPDATES
# ============================================

class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.update_task: Optional[asyncio.Task] = None
        logger.info("🔌 WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")

        if not self.update_task or self.update_task.done():
            self.update_task = asyncio.create_task(self.broadcast_prices())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")

        if not self.active_connections and self.update_task:
            self.update_task.cancel()

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"❌ Failed to send message: {str(e)}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send to websocket: {str(e)}")
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_prices(self):
        logger.info("📊 Starting price broadcast loop...")

        while self.active_connections:
            try:
                prices = await coingecko_service.get_prices()

                await self.broadcast({
                    "type": "price_update",
                    "data": prices,
                    "timestamp": datetime.utcnow().isoformat()
                })

                logger.info(f"📡 Broadcasted prices to {len(self.active_connections)} clients")

                await asyncio.sleep(10)

            except asyncio.CancelledError:
                logger.info("📊 Price broadcast loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in price broadcast: {str(e)}")
                await asyncio.sleep(10)

ws_manager = WebSocketConnectionManager()

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        prices = await coingecko_service.get_prices()
        await ws_manager.send_personal_message({
            "type": "initial_prices",
            "data": prices,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await ws_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)

# ============================================
# PORTFOLIO ENDPOINTS (real prices)
# ============================================

@api_router.get("/portfolio", tags=["portfolio"])
async def get_portfolio(user_id: str = Depends(get_current_user_id)):
    portfolios_collection = db_connection.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})

    if not portfolio_doc:
        portfolio = Portfolio(user_id=user_id)
        await portfolios_collection.insert_one(portfolio.dict())
        return {"portfolio": {"totalBalance": 0, "holdings": []}}

    holdings = portfolio_doc.get("holdings", [])
    prices = await coingecko_service.get_prices()

    total_balance = 0
    updated_holdings = []

    for holding in holdings:
        crypto = next((c for c in prices if c["symbol"].upper() == holding["symbol"].upper()), None)
        if crypto and "current_price" in crypto:
            current_price = crypto["current_price"]
            current_value = holding["amount"] * current_price
            total_balance += current_value
            updated_holdings.append({
                "symbol": holding["symbol"],
                "name": crypto.get("name", holding.get("name")),
                "amount": holding["amount"],
                "current_price": current_price,
                "value": round(current_value, 2),
                "allocation": 0
            })
        else:
            updated_holdings.append({
                **holding,
                "current_price": 0,
                "value": 0,
                "allocation": 0
            })

    for h in updated_holdings:
        h["allocation"] = round((h["value"] / total_balance * 100), 2) if total_balance > 0 else 0

    return {
        "portfolio": {
            "totalBalance": round(total_balance, 2),
            "holdings": updated_holdings
        }
    }

@api_router.get("/portfolio/holding/{symbol}", tags=["portfolio"])
async def get_holding(symbol: str, user_id: str = Depends(get_current_user_id)):
    portfolios_collection = db_connection.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holdings = portfolio_doc.get("holdings", [])
    holding = next((h for h in holdings if h["symbol"] == symbol.upper()), None)

    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    return {"holding": holding}

@api_router.post("/portfolio/holding", tags=["portfolio"])
async def add_holding(holding_data: HoldingCreate, user_id: str = Depends(get_current_user_id)):
    portfolios_collection = db_connection.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})

    if not portfolio_doc:
        portfolio = Portfolio(user_id=user_id)
        await portfolios_collection.insert_one(portfolio.dict())
        holdings = []
    else:
        holdings = portfolio_doc.get("holdings", [])

    # Use real price for value (optional – adjust as needed)
    prices = await coingecko_service.get_prices()
    crypto = next((c for c in prices if c["symbol"].upper() == holding_data.symbol.upper()), None)
    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")

    new_holding = {
        "symbol": holding_data.symbol.upper(),
        "name": holding_data.name,
        "amount": holding_data.amount,
        "value": holding_data.amount * crypto["current_price"],
        "allocation": 0
    }

    existing_idx = next((i for i, h in enumerate(holdings) if h["symbol"] == holding_data.symbol.upper()), None)

    if existing_idx is not None:
        holdings[existing_idx]["amount"] += holding_data.amount
        holdings[existing_idx]["value"] = holdings[existing_idx]["amount"] * crypto["current_price"]
    else:
        holdings.append(new_holding)

    await portfolios_collection.update_one(
        {"user_id": user_id},
        {"$set": {"holdings": holdings, "updated_at": datetime.utcnow()}}
    )

    return {"message": "Holding added successfully", "holding": new_holding}

@api_router.delete("/portfolio/holding/{symbol}", tags=["portfolio"])
async def delete_holding(symbol: str, user_id: str = Depends(get_current_user_id)):
    portfolios_collection = db_connection.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holdings = portfolio_doc.get("holdings", [])
    holdings = [h for h in holdings if h["symbol"] != symbol.upper()]

    await portfolios_collection.update_one(
        {"user_id": user_id},
        {"$set": {"holdings": holdings, "updated_at": datetime.utcnow()}}
    )

    return {"message": "Holding deleted successfully"}

# ============================================
# ORDER ENDPOINTS
# ============================================

@api_router.get("/orders", tags=["orders"])
async def get_orders(user_id: str = Depends(get_current_user_id)):
    orders_collection = db_connection.get_collection("orders")
    orders = await orders_collection.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    return {"orders": orders}

@api_router.post("/orders", tags=["orders"])
@limiter.limit("20/minute")
async def create_order(order_data: OrderCreate, request: Request, user_id: str = Depends(get_current_user_id)):
    orders_collection = db_connection.get_collection("orders")
    transactions_collection = db_connection.get_collection("transactions")

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

    transaction = Transaction(
        user_id=user_id,
        type="trade",
        amount=order_data.amount,
        symbol=order_data.trading_pair,
        description=f"{order_data.side.upper()} {order_data.amount} {order_data.trading_pair} @ {order_data.price}"
    )
    await transactions_collection.insert_one(transaction.dict())

    await log_audit(user_id, "ORDER_CREATED", resource=order.id, ip_address=request.client.host)

    return {"message": "Order created successfully", "order": order.dict()}

@api_router.get("/orders/{order_id}", tags=["orders"])
async def get_order(order_id: str, user_id: str = Depends(get_current_user_id)):
    orders_collection = db_connection.get_collection("orders")
    order = await orders_collection.find_one({"id": order_id, "user_id": user_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"order": order}

@api_router.post("/orders/{order_id}/cancel", tags=["orders"])
async def cancel_order(order_id: str, user_id: str = Depends(get_current_user_id)):
    orders_collection = db_connection.get_collection("orders")
    result = await orders_collection.update_one(
        {"id": order_id, "user_id": user_id, "status": "pending"},
        {"$set": {"status": "cancelled"}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Order not found or already processed")

    return {"message": "Order cancelled successfully"}

# ============================================
# TRANSACTION ENDPOINTS
# ============================================

@api_router.get("/transactions", tags=["transactions"])
async def get_transactions(limit: int = 50, offset: int = 0, user_id: str = Depends(get_current_user_id)):
    transactions_collection = db_connection.get_collection("transactions")
    transactions = await transactions_collection.find({"user_id": user_id})        .sort("created_at", -1)        .skip(offset)        .limit(limit)        .to_list(limit)

    total = await transactions_collection.count_documents({"user_id": user_id})

    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@api_router.get("/transactions/{transaction_id}", tags=["transactions"])
async def get_transaction(transaction_id: str, user_id: str = Depends(get_current_user_id)):
    transactions_collection = db_connection.get_collection("transactions")
    transaction = await transactions_collection.find_one({"id": transaction_id, "user_id": user_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {"transaction": transaction}

@api_router.post("/transactions", tags=["transactions"])
async def create_transaction(txn_data: TransactionCreate, user_id: str = Depends(get_current_user_id)):
    transactions_collection = db_connection.get_collection("transactions")
    transaction = Transaction(
        user_id=user_id,
        type=txn_data.type,
        amount=txn_data.amount,
        symbol=txn_data.symbol,
        description=txn_data.description
    )

    await transactions_collection.insert_one(transaction.dict())

    return {"message": "Transaction created successfully", "transaction": transaction.dict()}

@api_router.get("/transactions/stats/overview", tags=["transactions"])
async def get_transaction_stats(user_id: str = Depends(get_current_user_id)):
    transactions_collection = db_connection.get_collection("transactions")
    transactions = await transactions_collection.find({"user_id": user_id}).to_list(1000)

    total_deposits = sum(t["amount"] for t in transactions if t["type"] == "deposit")
    total_withdrawals = sum(t["amount"] for t in transactions if t["type"] == "withdrawal")
    total_trades = len([t for t in transactions if t["type"] == "trade"])

    return {
        "stats": {
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "total_trades": total_trades,
            "net_balance": total_deposits - total_withdrawals
        }
    }

# ============================================
# AUDIT LOG ENDPOINTS
# ============================================

@api_router.get("/audit-logs", tags=["audit"])
async def get_audit_logs(limit: int = 50, offset: int = 0, action: Optional[str] = None,
                        user_id: str = Depends(get_current_user_id)):
    audit_logs_collection = db_connection.get_collection("audit_logs")
    query = {"user_id": user_id}
    if action:
        query["action"] = action

    logs = await audit_logs_collection.find(query)        .sort("created_at", -1)        .skip(offset)        .limit(limit)        .to_list(limit)

    total = await audit_logs_collection.count_documents(query)

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@api_router.get("/audit-logs/summary", tags=["audit"])
async def get_audit_summary(days: int = 30, user_id: str = Depends(get_current_user_id)):
    audit_logs_collection = db_connection.get_collection("audit_logs")
    since = datetime.utcnow() - timedelta(days=days)

    logs = await audit_logs_collection.find({
        "user_id": user_id,
        "created_at": {"": since}
    }).to_list(1000)

    action_counts = {}
    for log in logs:
        action = log["action"]
        action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "summary": {
            "total_events": len(logs),
            "action_counts": action_counts,
            "period_days": days
        }
    }

@api_router.get("/audit-logs/export", tags=["audit"])
async def export_audit_logs(days: int = 90, user_id: str = Depends(get_current_user_id)):
    audit_logs_collection = db_connection.get_collection("audit_logs")
    since = datetime.utcnow() - timedelta(days=days)

    logs = await audit_logs_collection.find({
        "user_id": user_id,
        "created_at": {"": since}
    }).sort("created_at", -1).to_list(10000)

    return {"logs": logs, "count": len(logs)}

@api_router.get("/audit-logs/{log_id}", tags=["audit"])
async def get_audit_log(log_id: str, user_id: str = Depends(get_current_user_id)):
    audit_logs_collection = db_connection.get_collection("audit_logs")
    log = await audit_logs_collection.find_one({"id": log_id, "user_id": user_id})
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return {"log": log}

# ============================================
# LEGACY ENDPOINTS (optional – keep or remove)
# ============================================

@api_router.get("/", tags=["legacy"])
async def legacy_root():
    return {"message": "CryptoVault API v1.0", "status": "operational"}

@api_router.post("/status", tags=["legacy"])
async def create_status_check(data: dict):
    return {"message": "Status check received", "timestamp": datetime.utcnow().isoformat()}

@api_router.get("/status", tags=["legacy"])
async def get_status_checks():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ============================================
# INCLUDE ROUTER AND MIDDLEWARE
# ============================================

app.include_router(api_router)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.get_cors_origins_list(),
    allow_methods=["*"],
    allow_headers=["*"],
)
