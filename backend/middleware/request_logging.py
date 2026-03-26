"""
Comprehensive Request and Runtime Logging Middleware
Provides authentic, actionable logging for all API operations.
"""

import time
import uuid
import logging
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses with timing information.
    Includes:
    - Unique request IDs for correlation
    - Response times and performance metrics
    - Request/response sizes
    - User identification (if authenticated)
    - Status codes and error details
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.performance_threshold_ms = 1000  # Log slow requests > 1s
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.url.path
        query_string = request.url.query
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get user ID if authenticated (from cookie or header)
        user_id = "anonymous"
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, would decode JWT here
            user_id = "authenticated"
        
        # Log incoming request
        logger.info(
            f"→ {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_host,
                "user_id": user_id,
                "type": "request_start"
            }
        )
        
        try:
            # Call the endpoint
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the response
            status_code = response.status_code
            
            # Determine log level based on status code
            if status_code < 400:
                logger.info(
                    f"← {status_code} {method} {path} ({duration_ms:.1f}ms)",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "user_id": user_id,
                        "type": "request_complete"
                    }
                )
            elif status_code < 500:
                logger.warning(
                    f"← {status_code} {method} {path} ({duration_ms:.1f}ms) - Client error",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "user_id": user_id,
                        "type": "request_error"
                    }
                )
            else:
                logger.error(
                    f"← {status_code} {method} {path} ({duration_ms:.1f}ms) - Server error",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "user_id": user_id,
                        "type": "request_error"
                    }
                )
            
            # Log slow requests
            if duration_ms > self.performance_threshold_ms:
                logger.warning(
                    f"⚠️ Slow request: {method} {path} took {duration_ms:.0f}ms",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "duration_ms": duration_ms,
                        "threshold_ms": self.performance_threshold_ms,
                        "type": "performance_warning"
                    }
                )
            
            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"❌ {method} {path} failed after {duration_ms:.1f}ms: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "error": str(e),
                    "type": "request_exception"
                },
                exc_info=True
            )
            raise


class OperationLoggingMiddleware:
    """
    Helper class to log business operations throughout the app.
    Provides structured logging for key operations:
    - User authentication events
    - Financial transactions
    - Account changes
    - Security events
    """
    
    @staticmethod
    def log_auth_event(event_type: str, user_id: str, details: dict = None, **extra):
        """Log authentication events."""
        message = f"🔐 {event_type}"
        if event_type == "login":
            message = f"👤 User login: {user_id}"
        elif event_type == "logout":
            message = f"👋 User logout: {user_id}"
        elif event_type == "2fa_enabled":
            message = f"🔒 2FA enabled for {user_id}"
        elif event_type == "password_changed":
            message = f"🔑 Password changed for {user_id}"
        elif event_type == "session_created":
            message = f"📱 New session for {user_id}"
        
        log_data = {
            "event_type": "auth",
            "auth_event": event_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if details:
            log_data.update(details)
        log_data.update(extra)
        
        logger.info(message, extra=log_data)
    
    @staticmethod
    def log_transaction(operation: str, user_id: str, amount: float, currency: str, **extra):
        """Log financial transactions."""
        icons = {
            "deposit": "💰",
            "withdrawal": "💸",
            "transfer": "💱",
            "trade": "📈",
            "stake": "🎯"
        }
        icon = icons.get(operation, "💳")
        
        message = f"{icon} {operation.capitalize()}: {amount} {currency} for user {user_id}"
        
        log_data = {
            "event_type": "transaction",
            "operation": operation,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        log_data.update(extra)
        
        logger.info(message, extra=log_data)
    
    @staticmethod
    def log_security_event(event_type: str, user_id: str, details: str = None, **extra):
        """Log security-related events."""
        icons = {
            "failed_login": "❌",
            "failed_otp": "❌",
            "ip_change": "⚠️",
            "suspicious_activity": "🚨",
            "rate_limit": "🛑",
            "csrf_failure": "🔒",
        }
        icon = icons.get(event_type, "🔐")
        
        message = f"{icon} Security event [{event_type}]: {details or 'See extra data'}"
        
        log_data = {
            "event_type": "security",
            "security_event": event_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if details:
            log_data["details"] = details
        log_data.update(extra)
        
        logger.warning(message, extra=log_data)
    
    @staticmethod
    def log_error_event(endpoint: str, error_type: str, message: str, user_id: str = None, **extra):
        """Log error events with actionable information."""
        message_text = f"❌ {endpoint}: {error_type} - {message}"
        
        log_data = {
            "event_type": "error",
            "endpoint": endpoint,
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if user_id:
            log_data["user_id"] = user_id
        log_data.update(extra)
        
        logger.error(message_text, extra=log_data)


# Create singleton logger instance
operation_logger = OperationLoggingMiddleware()
