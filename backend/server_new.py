"""
CryptoVault API Server - Production Ready
Modular, well-organized FastAPI application with comprehensive error handling,
monitoring, and production-grade features.
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Set
from datetime import datetime
import logging
import asyncio
import uuid
import time
import sys
import json

# Configuration and database
from .config import settings
from .database import DatabaseConnection

# Routers
from .routers import auth, portfolio, trading, crypto, admin

# Services
from .coingecko_service import coingecko_service
from .websocket_feed import price_feed

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Dependencies
from . import dependencies

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

# ============================================
# RATE LIMITING
# ============================================

def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on IP and user."""
    client_ip = get_remote_address(request)
    
    try:
        from .auth import decode_token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload and payload.get("sub"):
                return f"{payload.get('sub')}:{client_ip}"
    except Exception:
        pass
    
    user_agent = request.headers.get("user-agent", "")
    return f"{client_ip}:{hash(user_agent) % 1000}"


limiter = Limiter(key_func=get_rate_limit_key)

# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI(
    title="CryptoVault API",
    version="1.0.0",
    description="Production-ready cryptocurrency trading platform with institutional-grade security",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# CORS CONFIGURATION
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# CUSTOM MIDDLEWARE
# ============================================

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
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
app.include_router(admin.router, prefix="/api")

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
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"])
async def health_check(request: Request):
    """Health check endpoint for monitoring and load balancers."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        if not db_connection or not db_connection.is_connected:
            logger.warning(
                "Health check failed: database disconnected",
                extra={"request_id": request_id, "type": "health_check"}
            )
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Perform actual health check
        await db_connection.health_check()
        
        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.environment,
            "version": "1.0.0",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(
            f"Health check failed: {str(e)}",
            extra={"request_id": request_id, "type": "health_check_error"},
            exc_info=True
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": "Health check failed",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/csrf", tags=["auth"])
async def get_csrf_token(request: Request):
    """Get CSRF token for form submissions."""
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
# WEBSOCKET FOR REAL-TIME PRICE UPDATES
# ============================================

class WebSocketConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.update_task: Optional[asyncio.Task] = None
        logger.info("🔌 WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ WebSocket connected. Total: {len(self.active_connections)}")

        if not self.update_task or self.update_task.done():
            self.update_task = asyncio.create_task(self.broadcast_prices())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"❌ WebSocket disconnected. Total: {len(self.active_connections)}")

        if not self.active_connections and self.update_task:
            self.update_task.cancel()

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

                logger.debug(f"📡 Broadcasted prices to {len(self.active_connections)} clients")
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
    """WebSocket endpoint for real-time price updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

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
            if db_connection and db_connection.is_connected:
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
                await collection.create_index("email", unique=True)
                await collection.create_index("last_login")
                logger.info("✅ Created indexes on users collection")
                
                # Index on portfolios
                collection = db_connection.get_collection("portfolios")
                await collection.create_index("user_id", unique=True)
                logger.info("✅ Created index on portfolios")
                
                # Index on orders
                collection = db_connection.get_collection("orders")
                await collection.create_index("user_id")
                await collection.create_index("created_at")
                logger.info("✅ Created indexes on orders")
                
                # Index on audit_logs
                collection = db_connection.get_collection("audit_logs")
                await collection.create_index("user_id")
                await collection.create_index("action")
                await collection.create_index("timestamp")
                logger.info("✅ Created indexes on audit_logs")
                
        except Exception as e:
            logger.warning(f"⚠️ Index creation failed (non-critical): {str(e)}")

        # Start WebSocket price feed
        try:
            asyncio.create_task(price_feed.start())
            logger.info("✅ WebSocket price feed started")
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
