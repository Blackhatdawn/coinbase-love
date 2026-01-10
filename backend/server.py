"""
Production-ready FastAPI server with proper startup checks and error handling.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import random
import asyncio

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

# Import auth utilities
from auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, generate_backup_codes, generate_2fa_secret
)

# Import dependencies
from dependencies import get_current_user_id, optional_current_user_id


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# DATABASE CONNECTION WITH HEALTH CHECKS
# ============================================

class DatabaseManager:
    """Manages MongoDB connection with health checks and retries."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._is_connected = False
    
    async def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """Establish database connection with retries."""
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔌 Connecting to MongoDB (attempt {attempt}/{max_retries})...")
                
                self.client = AsyncIOMotorClient(
                    settings.mongo_url,
                    maxPoolSize=settings.mongo_max_pool_size,
                    minPoolSize=settings.mongo_min_pool_size,
                    serverSelectionTimeoutMS=settings.mongo_server_selection_timeout_ms,
                    retryWrites=True,
                    retryReads=True
                )
                
                self.db = self.client[settings.db_name]
                
                # Perform health check
                await self.client.admin.command('ping')
                
                self._is_connected = True
                logger.info(f"✅ MongoDB connected: {settings.db_name}")
                logger.info(f"   Pool: {settings.mongo_min_pool_size}-{settings.mongo_max_pool_size} connections")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"❌ MongoDB connection failed: {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"⏳ Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.critical("💥 Failed to connect after all retries")
                    raise ConnectionError(f"MongoDB connection failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {str(e)}")
            self._is_connected = False
            return False
    
    async def disconnect(self):
        """Gracefully close database connection."""
        if self.client:
            logger.info("🔌 Closing MongoDB connection...")
            self.client.close()
            self._is_connected = False
            logger.info("✅ MongoDB disconnected")
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected


# Global database manager
db_manager = DatabaseManager()


# ============================================
# CREATE FASTAPI APP
# ============================================

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="CryptoVault API",
    version="1.0.0",
    description="Production-ready cryptocurrency trading platform"
)

# Add rate limit exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create API router
api_router = APIRouter(prefix="/api")


# ============================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize connections and perform health checks."""
    logger.info("="*70)
    logger.info("🚀 Starting CryptoVault API Server")
    logger.info("="*70)
    
    try:
        # Connect to database with health check
        await db_manager.connect()
        
        logger.info("="*70)
        logger.info("✅ Server startup complete!")
        logger.info(f"   Environment: {settings.environment}")
        logger.info(f"   Database: {settings.db_name}")
        logger.info(f"   JWT Secret: ***[{len(settings.jwt_secret)} chars]***")
        logger.info(f"   Rate Limit: {settings.rate_limit_per_minute} req/min")
        logger.info("="*70)
        
    except Exception as e:
        logger.critical(f"💥 Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown connections."""
    logger.info("="*70)
    logger.info("🛑 Shutting down CryptoVault API Server")
    logger.info("="*70)
    
    try:
        await db_manager.disconnect()
        logger.info("✅ Graceful shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}")


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 if healthy, 503 if database is down.
    """
    try:
        db_healthy = await db_manager.health_check()
        
        if not db_healthy:
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
    """Log an audit event."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        details=details
    )
    await db_manager.db.audit_logs.insert_one(audit_log.dict())


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@api_router.post("/auth/signup")
@limiter.limit("5/minute")  # Strict rate limit for signups
async def signup(user_data: UserCreate, request: Request):
    """Register a new user with email verification"""
    users_collection = db_manager.db.users
    portfolios_collection = db_manager.db.portfolios
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate verification tokens
    verification_code = generate_verification_code()  # 6-digit code
    verification_token = generate_verification_token()  # UUID token
    verification_expires = get_token_expiration(hours=24)
    
    # Create new user (email not verified yet)
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
    
    # Create empty portfolio
    portfolio = Portfolio(user_id=user.id)
    await portfolios_collection.insert_one(portfolio.dict())
    
    # Send verification email
    import os
    app_url = os.environ.get('APP_URL', 'http://localhost:3000')
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
    
    # Log audit event
    await log_audit(user.id, "USER_SIGNUP", ip_address=request.client.host)
    
    # Return user data (without session tokens - verification required first)
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


@api_router.post("/auth/login")
@limiter.limit("10/minute")  # Rate limit for login attempts
async def login(credentials: UserLogin, request: Request):
    """Login user"""
    users_collection = db_manager.db.users
    
    # Find user
    user_doc = await users_collection.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_doc)
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Log audit
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


@api_router.post("/auth/logout")
async def logout(request: Request, user_id: str = Depends(get_current_user_id)):
    """Logout user"""
    await log_audit(user_id, "USER_LOGOUT", ip_address=request.client.host)
    
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@api_router.get("/auth/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """Get current user profile"""
    users_collection = db_manager.db.users
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


@api_router.post("/auth/refresh")
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
    
    # Create new access token
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


@api_router.post("/auth/verify-email")
@limiter.limit("10/minute")  # Rate limit for verification attempts
async def verify_email(data: VerifyEmailRequest, request: Request):
    """Verify email with code or token"""
    users_collection = db_manager.db.users
    
    # Find user by verification code or token
    user_doc = await users_collection.find_one({
        "$or": [
            {"email_verification_code": data.token},
            {"email_verification_token": data.token}
        ]
    })
    
    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    user = User(**user_doc)
    
    # Check if already verified
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Check expiration
    if user.email_verification_expires < datetime.utcnow():
        raise HTTPException(
            status_code=400, 
            detail="Verification code expired. Please request a new one."
        )
    
    # Mark as verified and clear tokens
    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "email_verified": True,
            "email_verification_code": None,
            "email_verification_token": None,
            "email_verification_expires": None
        }}
    )
    
    # Create session tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Log audit event
    await log_audit(user.id, "EMAIL_VERIFIED")
    
    # Send welcome email
    import os
    app_url = os.environ.get('APP_URL', 'http://localhost:3000')
    subject, html_content, text_content = email_service.get_welcome_email(
        name=user.name,
        app_url=app_url
    )
    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )
    
    # Create response with cookies
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


@api_router.post("/auth/resend-verification")
@limiter.limit("3/minute")  # Strict rate limit for resend requests
async def resend_verification(data: ResendVerificationRequest, request: Request):
    """Resend verification email"""
    users_collection = db_manager.db.users
    
    # Find user
    user_doc = await users_collection.find_one({"email": data.email})
    if not user_doc:
        # Don't reveal if email exists
        return {"message": "If this email is registered, a verification email has been sent."}
    
    user = User(**user_doc)
    
    # Check if already verified
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new tokens
    verification_code = generate_verification_code()
    verification_token = generate_verification_token()
    verification_expires = get_token_expiration(hours=24)
    
    # Update user
    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "email_verification_code": verification_code,
            "email_verification_token": verification_token,
            "email_verification_expires": verification_expires
        }}
    )
    
    # Send email
    import os
    app_url = os.environ.get('APP_URL', 'http://localhost:3000')
    subject, html_content, text_content = email_service.get_verification_email(
        name=user.name,
        code=verification_code,
        token=verification_token,
        app_url=app_url
    )
    
    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )
    
    return {"message": "Verification email sent! Please check your inbox."}


@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Request password reset email"""
    users_collection = db_manager.db.users
    
    # Find user
    user_doc = await users_collection.find_one({"email": data.email})
    
    # Always return success (don't reveal if email exists)
    if not user_doc:
        return {"message": "If this email is registered, a password reset link has been sent."}
    
    user = User(**user_doc)
    
    # Generate reset token
    reset_token = generate_password_reset_token()
    reset_expires = get_token_expiration(hours=1)  # 1 hour expiration
    
    # Update user
    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "password_reset_token": reset_token,
            "password_reset_expires": reset_expires
        }}
    )
    
    # Send reset email
    import os
    app_url = os.environ.get('APP_URL', 'http://localhost:3000')
    reset_link = f"{app_url}/reset-password?token={reset_token}"
    
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
    
    # Log audit event
    await log_audit(user.id, "PASSWORD_RESET_REQUESTED")
    
    return {"message": "If this email is registered, a password reset link has been sent."}


@api_router.get("/auth/validate-reset-token/{token}")
async def validate_reset_token(token: str):
    """Validate if password reset token is valid"""
    users_collection = db_manager.db.users
    
    user_doc = await users_collection.find_one({"password_reset_token": token})
    
    if not user_doc:
        return {"valid": False, "message": "Invalid reset token"}
    
    user = User(**user_doc)
    
    # Check expiration
    if user.password_reset_expires < datetime.utcnow():
        return {"valid": False, "message": "Reset token expired"}
    
    return {"valid": True, "message": "Token is valid"}


@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password with valid token"""
    users_collection = db_manager.db.users
    
    # Find user by reset token
    user_doc = await users_collection.find_one({"password_reset_token": data.token})
    
    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user = User(**user_doc)
    
    # Check expiration
    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired. Please request a new one.")
    
    # Validate new password
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Update password and clear reset token
    new_password_hash = get_password_hash(data.new_password)
    
    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "password_hash": new_password_hash,
            "password_reset_token": None,
            "password_reset_expires": None,
            "failed_login_attempts": 0,  # Reset failed attempts
            "locked_until": None  # Unlock account
        }}
    )
    
    # Log audit event
    await log_audit(user.id, "PASSWORD_RESET_COMPLETED")
    
    return {"message": "Password reset successfully! You can now log in with your new password."}


# ============================================
# 2FA ENDPOINTS
# ============================================

@api_router.post("/auth/verify-email")
async def verify_email(data: dict):
    """Verify email (placeholder)"""
    return {"message": "Email verification not yet implemented"}


@api_router.post("/auth/2fa/setup")
async def setup_2fa(user_id: str = Depends(get_current_user_id)):
    """Setup 2FA for user"""
    users_collection = db_manager.db.users
    secret = generate_2fa_secret()
    
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"two_factor_secret": secret}}
    )
    
    return {
        "secret": secret,
        "qr_code_url": f"otpauth://totp/CryptoVault:{user_id}?secret={secret}&issuer=CryptoVault"
    }


@api_router.post("/auth/2fa/verify")
async def verify_2fa(data: TwoFactorVerify, user_id: str = Depends(get_current_user_id)):
    """Verify and enable 2FA"""
    users_collection = db_manager.db.users
    
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


@api_router.get("/auth/2fa/status")
async def get_2fa_status(user_id: str = Depends(get_current_user_id)):
    """Get 2FA status"""
    users_collection = db_manager.db.users
    user_doc = await users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"enabled": user_doc.get("two_factor_enabled", False)}


@api_router.post("/auth/2fa/disable")
async def disable_2fa(data: dict, user_id: str = Depends(get_current_user_id)):
    """Disable 2FA"""
    users_collection = db_manager.db.users
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {
            "two_factor_enabled": False,
            "two_factor_secret": None,
            "backup_codes": []
        }}
    )
    
    return {"message": "2FA disabled successfully"}


@api_router.post("/auth/2fa/backup-codes")
async def get_backup_codes(user_id: str = Depends(get_current_user_id)):
    """Get new backup codes"""
    users_collection = db_manager.db.users
    backup_codes = generate_backup_codes()
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"backup_codes": backup_codes}}
    )
    
    return {"codes": backup_codes}


# ============================================
# CRYPTOCURRENCY ENDPOINTS
# ============================================

# Mock cryptocurrency data
MOCK_CRYPTOS = [
    {"symbol": "BTC", "name": "Bitcoin", "price": 65000, "market_cap": 1200000000000, "volume_24h": 28000000000, "change_24h": 2.5},
    {"symbol": "ETH", "name": "Ethereum", "price": 3500, "market_cap": 420000000000, "volume_24h": 15000000000, "change_24h": 1.8},
    {"symbol": "USDT", "name": "Tether", "price": 1.0, "market_cap": 95000000000, "volume_24h": 45000000000, "change_24h": 0.01},
    {"symbol": "BNB", "name": "Binance Coin", "price": 580, "market_cap": 89000000000, "volume_24h": 2000000000, "change_24h": 0.9},
    {"symbol": "SOL", "name": "Solana", "price": 145, "market_cap": 62000000000, "volume_24h": 2500000000, "change_24h": 3.2},
    {"symbol": "XRP", "name": "Ripple", "price": 0.55, "market_cap": 29000000000, "volume_24h": 1200000000, "change_24h": -0.5},
    {"symbol": "USDC", "name": "USD Coin", "price": 1.0, "market_cap": 28000000000, "volume_24h": 5000000000, "change_24h": 0.0},
    {"symbol": "ADA", "name": "Cardano", "price": 0.48, "market_cap": 16800000000, "volume_24h": 350000000, "change_24h": 1.2},
    {"symbol": "DOGE", "name": "Dogecoin", "price": 0.08, "market_cap": 11500000000, "volume_24h": 450000000, "change_24h": -1.3},
    {"symbol": "TRX", "name": "TRON", "price": 0.12, "market_cap": 10500000000, "volume_24h": 280000000, "change_24h": 0.4},
]


@api_router.get("/crypto")
async def get_all_cryptocurrencies():
    """Get all cryptocurrencies"""
    cryptos = []
    for crypto in MOCK_CRYPTOS:
        variation = random.uniform(-0.02, 0.02)
        cryptos.append({
            **crypto,
            "price": crypto["price"] * (1 + variation),
            "last_updated": datetime.utcnow().isoformat()
        })
    
    return {"cryptocurrencies": cryptos}


@api_router.get("/crypto/{symbol}")
async def get_cryptocurrency(symbol: str):
    """Get specific cryptocurrency"""
    crypto = next((c for c in MOCK_CRYPTOS if c["symbol"] == symbol.upper()), None)
    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    
    variation = random.uniform(-0.02, 0.02)
    return {
        "cryptocurrency": {
            **crypto,
            "price": crypto["price"] * (1 + variation),
            "last_updated": datetime.utcnow().isoformat()
        }
    }


# ============================================
# PORTFOLIO ENDPOINTS  
# ============================================

@api_router.get("/portfolio")
async def get_portfolio(user_id: str = Depends(get_current_user_id)):
    """Get user portfolio"""
    portfolios_collection = db_manager.db.portfolios
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})
    
    if not portfolio_doc:
        portfolio = Portfolio(user_id=user_id)
        await portfolios_collection.insert_one(portfolio.dict())
        return {"portfolio": {"totalBalance": 0, "holdings": []}}
    
    holdings = portfolio_doc.get("holdings", [])
    total_balance = 0
    updated_holdings = []
    
    for holding in holdings:
        crypto = next((c for c in MOCK_CRYPTOS if c["symbol"] == holding["symbol"]), None)
        if crypto:
            current_value = holding["amount"] * crypto["price"]
            total_balance += current_value
            updated_holdings.append({
                **holding,
                "value": current_value,
                "allocation": 0
            })
    
    for holding in updated_holdings:
        holding["allocation"] = (holding["value"] / total_balance * 100) if total_balance > 0 else 0
    
    return {
        "portfolio": {
            "totalBalance": total_balance,
            "holdings": updated_holdings
        }
    }


@api_router.get("/portfolio/holding/{symbol}")
async def get_holding(symbol: str, user_id: str = Depends(get_current_user_id)):
    """Get specific holding"""
    portfolios_collection = db_manager.db.portfolios
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    holdings = portfolio_doc.get("holdings", [])
    holding = next((h for h in holdings if h["symbol"] == symbol.upper()), None)
    
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    return {"holding": holding}


@api_router.post("/portfolio/holding")
async def add_holding(holding_data: HoldingCreate, user_id: str = Depends(get_current_user_id)):
    """Add or update holding"""
    portfolios_collection = db_manager.db.portfolios
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})
    
    if not portfolio_doc:
        portfolio = Portfolio(user_id=user_id)
        await portfolios_collection.insert_one(portfolio.dict())
        holdings = []
    else:
        holdings = portfolio_doc.get("holdings", [])
    
    existing_idx = next((i for i, h in enumerate(holdings) if h["symbol"] == holding_data.symbol.upper()), None)
    
    crypto = next((c for c in MOCK_CRYPTOS if c["symbol"] == holding_data.symbol.upper()), None)
    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    
    new_holding = {
        "symbol": holding_data.symbol.upper(),
        "name": holding_data.name,
        "amount": holding_data.amount,
        "value": holding_data.amount * crypto["price"],
        "allocation": 0
    }
    
    if existing_idx is not None:
        holdings[existing_idx]["amount"] += holding_data.amount
        holdings[existing_idx]["value"] = holdings[existing_idx]["amount"] * crypto["price"]
    else:
        holdings.append(new_holding)
    
    await portfolios_collection.update_one(
        {"user_id": user_id},
        {"$set": {"holdings": holdings, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Holding added successfully", "holding": new_holding}


@api_router.delete("/portfolio/holding/{symbol}")
async def delete_holding(symbol: str, user_id: str = Depends(get_current_user_id)):
    """Delete holding"""
    portfolios_collection = db_manager.db.portfolios
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

@api_router.get("/orders")
async def get_orders(user_id: str = Depends(get_current_user_id)):
    """Get all orders for user"""
    orders_collection = db_manager.db.orders
    orders = await orders_collection.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    return {"orders": orders}


@api_router.post("/orders")
async def create_order(order_data: OrderCreate, request: Request, user_id: str = Depends(get_current_user_id)):
    """Create new order"""
    orders_collection = db_manager.db.orders
    transactions_collection = db_manager.db.transactions
    
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


@api_router.get("/orders/{order_id}")
async def get_order(order_id: str, user_id: str = Depends(get_current_user_id)):
    """Get specific order"""
    orders_collection = db_manager.db.orders
    order = await orders_collection.find_one({"id": order_id, "user_id": user_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"order": order}


@api_router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, user_id: str = Depends(get_current_user_id)):
    """Cancel order"""
    orders_collection = db_manager.db.orders
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

@api_router.get("/transactions")
async def get_transactions(limit: int = 50, offset: int = 0, user_id: str = Depends(get_current_user_id)):
    """Get transaction history"""
    transactions_collection = db_manager.db.transactions
    transactions = await transactions_collection.find({"user_id": user_id})\
        .sort("created_at", -1)\
        .skip(offset)\
        .limit(limit)\
        .to_list(limit)
    
    total = await transactions_collection.count_documents({"user_id": user_id})
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@api_router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str, user_id: str = Depends(get_current_user_id)):
    """Get specific transaction"""
    transactions_collection = db_manager.db.transactions
    transaction = await transactions_collection.find_one({"id": transaction_id, "user_id": user_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"transaction": transaction}


@api_router.post("/transactions")
async def create_transaction(txn_data: TransactionCreate, user_id: str = Depends(get_current_user_id)):
    """Create new transaction"""
    transactions_collection = db_manager.db.transactions
    transaction = Transaction(
        user_id=user_id,
        type=txn_data.type,
        amount=txn_data.amount,
        symbol=txn_data.symbol,
        description=txn_data.description
    )
    
    await transactions_collection.insert_one(transaction.dict())
    
    return {"message": "Transaction created successfully", "transaction": transaction.dict()}


@api_router.get("/transactions/stats/overview")
async def get_transaction_stats(user_id: str = Depends(get_current_user_id)):
    """Get transaction statistics"""
    transactions_collection = db_manager.db.transactions
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

@api_router.get("/audit-logs")
async def get_audit_logs(limit: int = 50, offset: int = 0, action: Optional[str] = None,
                        user_id: str = Depends(get_current_user_id)):
    """Get audit logs"""
    audit_logs_collection = db_manager.db.audit_logs
    query = {"user_id": user_id}
    if action:
        query["action"] = action
    
    logs = await audit_logs_collection.find(query)\
        .sort("created_at", -1)\
        .skip(offset)\
        .limit(limit)\
        .to_list(limit)
    
    total = await audit_logs_collection.count_documents(query)
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@api_router.get("/audit-logs/summary")
async def get_audit_summary(days: int = 30, user_id: str = Depends(get_current_user_id)):
    """Get audit log summary"""
    audit_logs_collection = db_manager.db.audit_logs
    since = datetime.utcnow() - timedelta(days=days)
    
    logs = await audit_logs_collection.find({
        "user_id": user_id,
        "created_at": {"$gte": since}
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


@api_router.get("/audit-logs/export")
async def export_audit_logs(days: int = 90, user_id: str = Depends(get_current_user_id)):
    """Export audit logs"""
    audit_logs_collection = db_manager.db.audit_logs
    since = datetime.utcnow() - timedelta(days=days)
    
    logs = await audit_logs_collection.find({
        "user_id": user_id,
        "created_at": {"$gte": since}
    }).sort("created_at", -1).to_list(10000)
    
    return {"logs": logs, "count": len(logs)}


@api_router.get("/audit-logs/{log_id}")
async def get_audit_log(log_id: str, user_id: str = Depends(get_current_user_id)):
    """Get specific audit log"""
    audit_logs_collection = db_manager.db.audit_logs
    log = await audit_logs_collection.find_one({"id": log_id, "user_id": user_id})
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return {"log": log}


# ============================================
# LEGACY ENDPOINTS
# ============================================

@api_router.get("/")
async def root():
    return {"message": "CryptoVault API v1.0", "status": "operational"}


@api_router.post("/status")
async def create_status_check(data: dict):
    """Legacy status check endpoint"""
    return {"message": "Status check received", "timestamp": datetime.utcnow().isoformat()}


@api_router.get("/status")
async def get_status_checks():
    """Legacy status check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ============================================
# INCLUDE ROUTER AND MIDDLEWARE
# ============================================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.get_cors_origins_list(),
    allow_methods=["*"],
    allow_headers=["*"],
)
