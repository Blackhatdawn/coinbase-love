"""
Production-ready FastAPI server with updated MongoDB connection management (health checks, exponential backoff,
timeouts, validation), real-time price integration in portfolio, proper root endpoint, and secure logout
with token blacklisting.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, status, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import List, Optional, Set, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import os

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
# DATABASE CONNECTION (full class from your original)
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

# Global database connection instance (top-level, no indent)
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

@app.get("/", tags=["Root"])
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
# STARTUP AND SHUTDOWN EVENTS (with TTL index)
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

        # Create TTL index for MongoDB blacklist fallback auto-cleanup
        try:
            collection = db_connection.get_collection("blacklisted_tokens")
            await collection.create_index("expires_at", expireAfterSeconds=0)
            logger.info("✅ Ensured TTL index on blacklisted_tokens.expires_at")
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

@app.get("/health")
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
# UPDATED LOGOUT ENDPOINT (secure with blacklisting)
# ============================================

@api_router.post("/auth/logout")
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

# ============================================
# YOUR OTHER ENDPOINTS (add them here)
# ============================================

# Example portfolio endpoint (from your code – add the rest similarly)
@api_router.get("/portfolio")
async def get_portfolio(user_id: str = Depends(get_current_user_id)):
    global db_connection
    portfolios_collection = db_connection.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})

    if not portfolio_doc:
        portfolio = Portfolio(user_id=user_id)
        await portfolios_collection.insert_one(portfolio.dict())
        return {"portfolio": {"totalBalance": 0, "holdings": []}}

    holdings = portfolio_doc.get("holdings", [])
    prices = await coingecko_service.get_prices()  # Real prices

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

# Add your other endpoints here (signup, login, crypto, orders, etc.)
# Use db_connection.get_collection("name") for DB access

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
