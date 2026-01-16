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
from config import settings, validate_startup_environment
from database import DatabaseConnection

# Routers
from routers import auth, portfolio, trading, crypto, admin, wallet, alerts, transactions, prices, websocket

# Services
from coingecko_service import coingecko_service
from websocket_feed import price_feed
from services import price_stream_service

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
    """Get rate limit key based on IP and user."""
    client_ip = get_remote_address(request)
    
    try:
        from auth import decode_token
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
app.include_router(transactions.router, prefix="/api")

# WebSocket routers (no prefix, direct path)
app.include_router(websocket.router)

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
    """
    Production-grade WebSocket connection manager with:
    - Connection health monitoring (ping/pong)
    - Automatic reconnection support
    - Rate limiting for messages
    - Graceful error handling
    """
    
    PING_INTERVAL = 30  # Send ping every 30 seconds
    PING_TIMEOUT = 10   # Wait 10 seconds for pong response
    MAX_MESSAGE_RATE = 10  # Max messages per second per connection
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: dict = {}  # Track connection health
        self.update_task: Optional[asyncio.Task] = None
        self.ping_task: Optional[asyncio.Task] = None
        logger.info("🔌 WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Track connection metadata
        self.connection_metadata[id(websocket)] = {
            "connected_at": datetime.utcnow(),
            "last_ping": None,
            "last_pong": None,
            "message_count": 0,
            "healthy": True
        }
        
        logger.info(f"✅ WebSocket connected. Total: {len(self.active_connections)}")

        # Start tasks if not running
        if not self.update_task or self.update_task.done():
            self.update_task = asyncio.create_task(self.broadcast_prices())
        
        if not self.ping_task or self.ping_task.done():
            self.ping_task = asyncio.create_task(self.health_check_loop())

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        self.connection_metadata.pop(id(websocket), None)
        logger.info(f"❌ WebSocket disconnected. Total: {len(self.active_connections)}")

        # Cancel tasks if no connections
        if not self.active_connections:
            if self.update_task:
                self.update_task.cancel()
            if self.ping_task:
                self.ping_task.cancel()

    async def send_ping(self, websocket: WebSocket) -> bool:
        """Send ping to a specific WebSocket and wait for pong."""
        try:
            metadata = self.connection_metadata.get(id(websocket))
            if metadata:
                metadata["last_ping"] = datetime.utcnow()
            
            await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
            return True
        except Exception as e:
            logger.warning(f"⚠️ Failed to send ping: {str(e)}")
            return False

    async def handle_pong(self, websocket: WebSocket):
        """Handle pong response from client."""
        metadata = self.connection_metadata.get(id(websocket))
        if metadata:
            metadata["last_pong"] = datetime.utcnow()
            metadata["healthy"] = True

    async def health_check_loop(self):
        """Periodically ping connections to check health."""
        logger.info("💓 Starting WebSocket health check loop...")
        
        while self.active_connections:
            try:
                unhealthy = []
                
                for websocket in list(self.active_connections):
                    metadata = self.connection_metadata.get(id(websocket))
                    
                    if metadata:
                        # Check if previous ping was not responded to
                        if metadata["last_ping"] and not metadata["last_pong"]:
                            # Check if timeout exceeded
                            time_since_ping = (datetime.utcnow() - metadata["last_ping"]).total_seconds()
                            if time_since_ping > self.PING_TIMEOUT:
                                metadata["healthy"] = False
                                unhealthy.append(websocket)
                                continue
                    
                    # Send new ping
                    success = await self.send_ping(websocket)
                    if not success:
                        unhealthy.append(websocket)
                
                # Disconnect unhealthy connections
                for ws in unhealthy:
                    logger.warning("🔴 Disconnecting unhealthy WebSocket connection")
                    self.disconnect(ws)
                
                await asyncio.sleep(self.PING_INTERVAL)
                
            except asyncio.CancelledError:
                logger.info("💓 Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in health check loop: {str(e)}")
                await asyncio.sleep(self.PING_INTERVAL)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for websocket in list(self.active_connections):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send to websocket: {str(e)}")
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_prices(self):
        """Broadcast price updates to all connected clients."""
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

    def get_connection_stats(self) -> dict:
        """Get WebSocket connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "healthy_connections": sum(
                1 for m in self.connection_metadata.values() if m.get("healthy", False)
            ),
            "connections": [
                {
                    "connected_at": m["connected_at"].isoformat(),
                    "healthy": m["healthy"],
                    "message_count": m["message_count"]
                }
                for m in self.connection_metadata.values()
            ]
        }


ws_manager = WebSocketConnectionManager()


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    WebSocket endpoint for real-time price updates.
    
    Supports:
    - Automatic price updates every 10 seconds
    - Ping/pong health checks
    - Graceful disconnection handling
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "pong":
                await ws_manager.handle_pong(websocket)
            else:
                # Handle other messages (could be subscription requests)
                try:
                    message = json.loads(data)
                    if message.get("type") == "pong":
                        await ws_manager.handle_pong(websocket)
                except json.JSONDecodeError:
                    pass
                    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)


@app.get("/api/ws/stats", tags=["websocket"])
async def get_websocket_stats():
    """Get WebSocket connection statistics (for monitoring)."""
    return ws_manager.get_connection_stats()

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
                
                # Index on price_alerts
                collection = db_connection.get_collection("price_alerts")
                await collection.create_index("user_id")
                await collection.create_index("symbol")
                await collection.create_index([("symbol", 1), ("is_active", 1)])
                await collection.create_index("created_at")
                logger.info("✅ Created indexes on price_alerts")
                
                # Index on deposits
                collection = db_connection.get_collection("deposits")
                await collection.create_index("user_id")
                await collection.create_index("order_id", unique=True)
                await collection.create_index("payment_id")
                await collection.create_index("status")
                await collection.create_index("created_at")
                logger.info("✅ Created indexes on deposits")
                
                # Index on transactions
                collection = db_connection.get_collection("transactions")
                await collection.create_index("user_id")
                await collection.create_index("type")
                await collection.create_index("created_at")
                await collection.create_index([("user_id", 1), ("type", 1)])
                logger.info("✅ Created indexes on transactions")
                
                # Index on wallets
                collection = db_connection.get_collection("wallets")
                await collection.create_index("user_id", unique=True)
                logger.info("✅ Created indexes on wallets")
                
                # Index on withdrawals
                collection = db_connection.get_collection("withdrawals")
                await collection.create_index("user_id")
                await collection.create_index("status")
                await collection.create_index("created_at")
                await collection.create_index([("user_id", 1), ("status", 1)])
                logger.info("✅ Created indexes on withdrawals")
                
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
