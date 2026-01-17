"""
CryptoVault API Server - Production Ready
Modular, well-organized FastAPI application with comprehensive error handling,
monitoring, and production-grade features.
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, Set
from datetime import datetime
import logging
import asyncio
import uuid
import time
import sys
import json

# Configuration and database
from config import settings, validate_startup_environment
from database import DatabaseConnection

# Routers
from routers import auth, portfolio, trading, crypto, admin, wallet, alerts, transactions, prices, websocket, transfers, users, notifications

# Services
from coingecko_service import coingecko_service
from websocket_feed import price_feed
from services import price_stream_service

# Enhanced services
from socketio_server import socketio_manager
from redis_enhanced import redis_enhanced

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Dependencies
import dependencies

# ============================================
# SENTRY INTEGRATION (Error Tracking)
# ============================================

if settings.is_sentry_available():
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR),
        ],
        send_default_pii=False,  # Don't send PII data
        attach_stacktrace=True,
        max_breadcrumbs=50,
        before_send=lambda event, hint: event if settings.environment != 'development' else None,
    )
    print("✅ Sentry error tracking initialized")

# ============================================
# LOGGING CONFIGURATION
# ============================================

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""
    
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        for field in ["request_id", "type", "method", "path", "status_code", 
                      "duration_ms", "error_type", "error_code", "user_id", "action"]:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


if settings.environment == "production":
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("JSON logging configured for production")
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

# ============================================
# MIDDLEWARE CLASSES
# ============================================

class RequestIDMiddleware:
    """Add unique request ID for correlation and tracking."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        request_id = str(uuid.uuid4())
        scope["request_id"] = request_id
        
        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode()
                message["headers"] = [(k, v) for k, v in headers.items()]
            await send(message)
        
        start_time = time.time()
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": scope.get("method"),
                "path": scope.get("path"),
                "client": scope.get("client", ["UNKNOWN", 0])[0],
                "type": "request_start"
            }
        )
        
        try:
            await self.app(scope, receive, send_with_request_id)
            duration = time.time() - start_time
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "duration_ms": round(duration * 1000, 2),
                    "type": "request_complete"
                }
            )
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "duration_ms": round(duration * 1000, 2),
                    "error_type": type(exc).__name__,
                    "type": "request_error"
                },
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware:
    """Add security headers to all responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                security_headers = {
                    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                    b"x-frame-options": b"DENY",
                    b"x-content-type-options": b"nosniff",
                    b"x-xss-protection": b"1; mode=block",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
                }
                
                headers.update(security_headers)
                message["headers"] = [(k, v) for k, v in headers.items()]
            
            await send(message)
        
        await self.app(scope, receive, send_with_security_headers)


class TimeoutMiddleware:
    """Add timeout protection to requests."""
    
    def __init__(self, app, timeout_seconds: int = 30):
        self.app = app
        self.timeout_seconds = timeout_seconds
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        try:
            await asyncio.wait_for(
                self.app(scope, receive, send),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout after {self.timeout_seconds} seconds")
            response = JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )
            await response(scope, receive, send)


class RateLimitHeadersMiddleware:
    """Add rate limit headers to responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        async def send_with_rate_limit_headers(message):
            if message["type"] == "http.response.start":
                # Get existing headers as a list (preserve duplicates like set-cookie)
                existing_headers = list(message.get("headers", []))
                
                # Add rate limit headers
                rate_limit_headers = [
                    (b"x-ratelimit-limit", str(settings.rate_limit_per_minute).encode()),
                    (b"x-ratelimit-policy", f"{settings.rate_limit_per_minute};w=60".encode()),
                ]
                
                # Append new headers (don't convert to dict which removes duplicates)
                existing_headers.extend(rate_limit_headers)
                message["headers"] = existing_headers
            
            await send(message)
        
        await self.app(scope, receive, send_with_rate_limit_headers)


# ============================================
# RATE LIMITING
# ============================================

def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on IP and user (from Authorization header or cookies)."""
    client_ip = get_remote_address(request)

    try:
        from auth import decode_token

        # Try Authorization header first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload and payload.get("sub"):
                logger.debug(f"Rate limit key from Authorization header for user {payload.get('sub')}")
                return f"{payload.get('sub')}:{client_ip}"

        # Fall back to access_token cookie (cookie-based auth)
        access_token_cookie = request.cookies.get("access_token")
        if access_token_cookie:
            try:
                payload = decode_token(access_token_cookie)
                if payload and payload.get("sub"):
                    logger.debug(f"Rate limit key from cookie for user {payload.get('sub')}")
                    return f"{payload.get('sub')}:{client_ip}"
            except Exception as e:
                logger.debug(f"Failed to decode token from cookie: {e}")
    except Exception as e:
        logger.debug(f"Error deriving rate limit key from auth: {e}")

    # Fallback: use IP and user-agent hash
    user_agent = request.headers.get("user-agent", "")
    fallback_key = f"{client_ip}:{hash(user_agent) % 1000}"
    logger.debug(f"Rate limit key from fallback (IP+UA): {fallback_key}")
    return fallback_key


limiter = Limiter(key_func=get_rate_limit_key)

# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI(
    title="CryptoVault API",
    version="1.0.0",
    description="Production-ready cryptocurrency trading platform with institutional-grade security",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# GLOBAL EXCEPTION HANDLERS (Error Standardization)
# ============================================

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardize HTTP exception responses to match frontend error interface.
    Converts FastAPI HTTPException to consistent error format.
    """
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }

    error_code = error_code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": str(exc.detail) if exc.detail else "An error occurred",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions and return standardized error format.
    Logs the full exception for debugging.
    """
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    logger.error(
        f"🔴 Unhandled exception: {str(exc)}",
        extra={
            "type": "error",
            "error_type": type(exc).__name__,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


# Register global exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ============================================
# CORS CONFIGURATION
# ============================================

# Get CORS origins from settings
cors_origins = settings.get_cors_origins_list()

# Important: When using allow_credentials=True with cross-site auth, cannot use ["*"]
# Browsers will reject credentialed requests with wildcard CORS
# The config validation will raise an error in production if this is misconfigured
if cors_origins == ["*"]:
    if settings.environment == 'development':
        logger.warning(
            "⚠️ DEVELOPMENT: CORS_ORIGINS is set to '*' - cookie-based authentication may not work "
            "with cross-origin requests. For production, set CORS_ORIGINS to specific origins."
        )
    else:
        logger.warning(
            "⚠️ Wildcard CORS detected - authentication may fail in cross-origin scenarios"
        )

# Apply CORS middleware with credentials for authenticated endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # Required for session/cookie auth
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token", "Accept", "Accept-Language"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ============================================
# COMPRESSION MIDDLEWARE
# ============================================

# Add Brotli compression for better compression ratios
try:
    from fastapi.middleware.gzip import GZipMiddleware
    import brotli
    
    # Note: Brotli is preferred over GZip for better compression
    # Most modern browsers support Brotli (br encoding)
    # GZip is kept as fallback
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    logger.info("✅ GZip compression middleware enabled (min size: 1000 bytes)")
except ImportError:
    logger.warning("⚠️ Compression middleware not available")

# ============================================
# CUSTOM MIDDLEWARE
# ============================================

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitHeadersMiddleware)
app.add_middleware(TimeoutMiddleware, timeout_seconds=settings.request_timeout_seconds)

# ============================================
# DATABASE CONNECTION
# ============================================

db_connection: Optional[DatabaseConnection] = None

# ============================================
# INCLUDE ROUTERS
# ============================================

app.include_router(auth.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(trading.router, prefix="/api")
app.include_router(crypto.router, prefix="/api")
app.include_router(prices.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(wallet.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(transfers.router, prefix="/api")
app.include_router(users.router, prefix="/api")

# WebSocket routers (no prefix, direct path)
app.include_router(websocket.router)

# ============================================
# SOCKET.IO INTEGRATION
# ============================================

# Mount Socket.IO ASGI app for real-time communication
from socketio import ASGIApp
socket_app = ASGIApp(socketio_manager.sio, app)

# Socket.IO endpoints will be available at /socket.io/
logger.info("✅ Socket.IO mounted at /socket.io/")

# ============================================
# ROOT & HEALTH ENDPOINTS
# ============================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "🚀 CryptoVault API is live and running!",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "openapi": "/api/openapi.json",
        "health": "/health",
        "ping": "/ping",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ping", tags=["health"])
@app.get("/api/ping", tags=["health"])
async def ping():
    """Simple ping endpoint that doesn't require database connection. For health checks and keep-alive."""
    return {
        "status": "ok",
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"])
async def health_check(request: Request):
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 if API is running, even if database is temporarily unavailable.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Basic health - API is running
    health_status = {
        "status": "healthy",
        "api": "running",
        "environment": settings.environment,
        "version": "1.0.0",
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Check database (non-critical for API health)
    try:
        if db_connection and db_connection.is_connected:
            # Try quick database ping with timeout
            try:
                await asyncio.wait_for(
                    db_connection.health_check(),
                    timeout=2.0  # Quick timeout
                )
                health_status["database"] = "connected"
            except asyncio.TimeoutError:
                health_status["database"] = "slow"
                logger.warning("Database health check timed out")
            except Exception as e:
                health_status["database"] = "error"
                logger.warning(f"Database health check error: {str(e)}")
        else:
            health_status["database"] = "initializing"
            logger.info("Database connection not yet established")
    except Exception as e:
        health_status["database"] = "unavailable"
        logger.warning(f"Database check failed: {str(e)}")

    # Return 200 OK as long as API is running
    # This allows health checks to pass during database initialization
    return health_status


@app.get("/csrf", tags=["auth"])
async def get_csrf_token(request: Request):
    """Get CSRF token for form submissions."""
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = str(uuid.uuid4())
        response = JSONResponse({"csrf_token": csrf_token})
        same_site = "none" if settings.use_cross_site_cookies else "lax"
        secure = (settings.environment == "production") or settings.use_cross_site_cookies
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=True,
            secure=secure,
            samesite=same_site,
            max_age=3600,
            path="/"
        )
        return response
    return {"csrf_token": csrf_token}

# ============================================
# STARTUP & SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global db_connection
    
    logger.info("="*70)
    logger.info("🚀 Starting CryptoVault API Server")
    logger.info("="*70)

    try:
        # Validate environment configuration
        try:
            validate_startup_environment()
            logger.info("✅ Environment validation passed")
        except Exception as e:
            logger.error(f"❌ Environment validation failed: {str(e)}")
            raise
        
        # Connect to database
        db_connection = DatabaseConnection(
            mongo_url=settings.mongo_url,
            db_name=settings.db_name
        )
        await db_connection.connect()
        
        # Set global database connection for dependencies
        dependencies.set_db_connection(db_connection)
        dependencies.set_limiter(limiter)
        
        # Create database indexes
        try:
            if db_connection is not None:
                db_is_connected = db_connection.is_connected
            else:
                db_is_connected = False
            
            if db_is_connected:
                # TTL index for login attempts
                collection = db_connection.get_collection("login_attempts")
                await collection.create_index("timestamp", expireAfterSeconds=30*24*60*60)
                logger.info("✅ Created TTL index on login_attempts")
                
                # TTL index for blacklisted tokens
                collection = db_connection.get_collection("blacklisted_tokens")
                await collection.create_index("expires_at", expireAfterSeconds=0)
                logger.info("✅ Created TTL index on blacklisted_tokens")
                
                # Index on users email
                collection = db_connection.get_collection("users")
                await collection.create_index("id", unique=True)
                await collection.create_index("email", unique=True)
                await collection.create_index("last_login")
                logger.info("✅ Created indexes on users collection")

                # Index on portfolios
                collection = db_connection.get_collection("portfolios")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id", unique=True)
                logger.info("✅ Created index on portfolios")

                # Index on orders
                collection = db_connection.get_collection("orders")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id")
                await collection.create_index("created_at")
                logger.info("✅ Created indexes on orders")

                # Index on audit_logs
                collection = db_connection.get_collection("audit_logs")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id")
                await collection.create_index("action")
                await collection.create_index("timestamp")
                logger.info("✅ Created indexes on audit_logs")

                # Index on price_alerts
                collection = db_connection.get_collection("price_alerts")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id")
                await collection.create_index("symbol")
                await collection.create_index([("symbol", 1), ("is_active", 1)])
                await collection.create_index("created_at")
                logger.info("✅ Created indexes on price_alerts")

                # Index on deposits
                collection = db_connection.get_collection("deposits")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id")
                await collection.create_index("order_id", unique=True)
                await collection.create_index("payment_id")
                await collection.create_index("status")
                await collection.create_index("created_at")
                logger.info("✅ Created indexes on deposits")

                # Index on transactions
                collection = db_connection.get_collection("transactions")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id")
                await collection.create_index("type")
                await collection.create_index("created_at")
                await collection.create_index([("user_id", 1), ("type", 1)])
                logger.info("✅ Created indexes on transactions")

                # Index on wallets
                collection = db_connection.get_collection("wallets")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id", unique=True)
                logger.info("✅ Created indexes on wallets")

                # Index on withdrawals
                collection = db_connection.get_collection("withdrawals")
                await collection.create_index("id", unique=True)
                await collection.create_index("user_id")
                await collection.create_index("status")
                await collection.create_index("created_at")
                await collection.create_index([("user_id", 1), ("status", 1)])
                logger.info("✅ Created indexes on withdrawals")

                # Index on sessions (auto-expire)
                collection = db_connection.get_collection("sessions")
                await collection.create_index("id", unique=True)
                await collection.create_index("session_id", unique=True)
                await collection.create_index("user_id")
                await collection.create_index("expires_at", expireAfterSeconds=0)
                logger.info("✅ Created indexes on sessions")
                
        except Exception as e:
            logger.warning(f"⚠️ Index creation failed (non-critical): {str(e)}")

        # Start real-time price stream service (PRIMARY)
        try:
            await price_stream_service.start()
            logger.info("✅ Real-time price stream service started (CoinCap WebSocket)")
        except Exception as e:
            logger.warning(f"⚠️ Price stream service failed to start: {str(e)}")

        # Start WebSocket price feed (FALLBACK)
        try:
            asyncio.create_task(price_feed.start())
            logger.info("✅ WebSocket price feed started (fallback)")
        except Exception as e:
            logger.warning(f"⚠️ Price feed failed to start: {str(e)}")

        logger.info("="*70)
        logger.info("✅ Server startup complete!")
        logger.info(f"📍 Environment: {settings.environment}")
        logger.info(f"💾 Database: {settings.db_name}")
        logger.info(f"🔐 JWT Algorithm: {settings.jwt_algorithm}")
        logger.info(f"⏱️ Rate Limit: {settings.rate_limit_per_minute} req/min")
        logger.info("="*70)

    except Exception as e:
        logger.critical(f"💥 Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global db_connection
    
    logger.info("="*70)
    logger.info("🛑 Shutting down CryptoVault API Server")
    logger.info("="*70)

    # Stop real-time price stream service
    try:
        await price_stream_service.stop()
        logger.info("✅ Real-time price stream service stopped")
    except Exception as e:
        logger.warning(f"⚠️ Price stream service stop error: {str(e)}")

    # Stop WebSocket price feed
    try:
        await price_feed.stop()
        logger.info("✅ WebSocket price feed stopped")
    except Exception as e:
        logger.warning(f"⚠️ Price feed stop error: {str(e)}")
    
    # Disconnect database
    if db_connection:
        await db_connection.disconnect()
    
    logger.info("✅ Graceful shutdown complete")
