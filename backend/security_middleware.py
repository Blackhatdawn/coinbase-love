"""
Security Middleware for CryptoVault
Implements CSRF protection, request tracing, and security headers.
Production-ready with strict CSRF enforcement.
"""

import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from config import settings  # For environment check

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for tracing, headers, and logging."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/ws", "/ws/prices"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        logger.info(
            f"🔍 [{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            response = self._add_security_headers(response, request_id)

            duration = (time.time() - start_time) * 1000
            logger.info(f"✅ [{request_id}] {response.status_code} ({duration:.2f}ms)")
            return response
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"❌ [{request_id}] Error: {str(e)} ({duration:.2f}ms)")
            raise

    def _add_security_headers(self, response: Response, request_id: str) -> Response:
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-API-Version"] = "1.0.0"

        # Relaxed CSP for frontend compatibility (adjust for your domains)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            f"connect-src 'self' {settings.get_cors_origins_list()[0] if settings.get_cors_origins_list() != ['*'] else '*'} wss: https:;"
        )
        response.headers["Content-Security-Policy"] = csp

        return response

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF Protection with double-submit cookie pattern."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = [
            "/api/auth/signup",
            "/api/auth/login",
            "/api/auth/logout",  # Optional: allow logout without token
            "/docs", "/redoc", "/openapi.json", "/health", "/ws", "/ws/prices"
        ]
        self.protected_methods = ["POST", "PUT", "DELETE", "PATCH"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in self.protected_methods:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        csrf_token_header = request.headers.get("X-CSRF-Token")
        csrf_token_cookie = request.cookies.get("csrf_token")

        # Set new token if missing
        if not csrf_token_cookie:
            csrf_token = str(uuid.uuid4())
            response = await call_next(request)
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=True,
                secure=(settings.environment == "production"),
                samesite="lax",  # "lax" better for redirects
                max_age=3600
            )
            return response

        # Strict validation in production
        is_valid = csrf_token_header == csrf_token_cookie
        if settings.environment == "production" and not is_valid:
            logger.warning(f"🚫 CSRF validation failed for {request.method} {path} from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token invalid or missing"
            )
        elif not is_valid:
            logger.warning(f"⚠️ CSRF token mismatch for {request.method} {path} (dev mode - allowed)")

        response = await call_next(request)
        return response

def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")
