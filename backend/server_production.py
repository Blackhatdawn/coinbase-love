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

# Import configuration
from config import settings

# Import models
from models import (
    User, UserCreate, UserLogin, UserResponse,
    Cryptocurrency, Portfolio, Holding, HoldingCreate,
    Order, OrderCreate, Transaction, TransactionCreate,
    AuditLog, TwoFactorSetup, TwoFactorVerify, BackupCodes
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

app = FastAPI(
    title="CryptoVault API",
    version="1.0.0",
    description="Production-ready cryptocurrency trading platform"
)

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
async def signup(user_data: UserCreate, request: Request):
    """Register a new user"""
    users_collection = db_manager.db.users
    portfolios_collection = db_manager.db.portfolios
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password)
    )
    
    await users_collection.insert_one(user.dict())
    
    # Create empty portfolio
    portfolio = Portfolio(user_id=user.id)
    await portfolios_collection.insert_one(portfolio.dict())
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Log audit event
    await log_audit(user.id, "USER_SIGNUP", ip_address=request.client.host)
    
    # Create response
    response = JSONResponse(content={
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    })
    
    # Set secure cookies
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


@api_router.post("/auth/login")
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