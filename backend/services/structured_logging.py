"""
Enhanced Structured Logging Configuration
JSON logging with contextual information
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
import traceback


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add module and function info
        if record.module:
            log_data["module"] = record.module
        if record.funcName:
            log_data["function"] = record.funcName
        if record.lineno:
            log_data["line"] = record.lineno
        
        # Add process/thread info
        log_data["process"] = record.process
        log_data["thread"] = record.thread
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'ip_address'):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, 'method'):
            log_data["method"] = record.method
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add stack info if present
        if record.stack_info:
            log_data["stack_info"] = record.stack_info
        
        return json.dumps(log_data)


class RequestContextFilter(logging.Filter):
    """
    Add request context to log records
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context if available"""
        # These will be set by middleware
        if not hasattr(record, 'request_id'):
            record.request_id = None
        if not hasattr(record, 'user_id'):
            record.user_id = None
        if not hasattr(record, 'ip_address'):
            record.ip_address = None
        
        return True


def setup_structured_logging(
    level: str = "INFO",
    enable_json: bool = True
) -> logging.Logger:
    """
    Setup structured logging for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Enable JSON formatting
        
    Returns:
        Configured logger
    """
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter
    if enable_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    # Add filter for request context
    handler.addFilter(RequestContextFilter())
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# ============================================
# LOGGER HELPERS
# ============================================

def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    user_id: str = None,
    ip_address: str = None,
    request_id: str = None
):
    """Log API request with context"""
    extra = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "user_id": user_id,
        "ip_address": ip_address,
        "request_id": request_id
    }
    
    if status_code >= 500:
        logger.error(f"API request failed: {method} {endpoint}", extra=extra)
    elif status_code >= 400:
        logger.warning(f"API request error: {method} {endpoint}", extra=extra)
    else:
        logger.info(f"API request: {method} {endpoint}", extra=extra)


def log_external_api_call(
    logger: logging.Logger,
    service: str,
    endpoint: str,
    success: bool,
    duration_ms: float,
    error: str = None
):
    """Log external API call"""
    extra = {
        "service": service,
        "endpoint": endpoint,
        "success": success,
        "duration_ms": duration_ms
    }
    
    if success:
        logger.info(f"External API call succeeded: {service}", extra=extra)
    else:
        extra["error"] = error
        logger.error(f"External API call failed: {service}", extra=extra)


def log_database_query(
    logger: logging.Logger,
    collection: str,
    operation: str,
    duration_ms: float,
    success: bool,
    error: str = None
):
    """Log database query"""
    extra = {
        "collection": collection,
        "operation": operation,
        "duration_ms": duration_ms,
        "success": success
    }
    
    if not success:
        extra["error"] = error
        logger.error(f"Database query failed: {collection}.{operation}", extra=extra)
    elif duration_ms > 1000:  # Slow query
        logger.warning(f"Slow database query: {collection}.{operation}", extra=extra)
    else:
        logger.debug(f"Database query: {collection}.{operation}", extra=extra)


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    user_id: str = None,
    ip_address: str = None,
    details: Dict[str, Any] = None
):
    """Log security event"""
    extra = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details or {}
    }
    
    logger.warning(f"Security event: {event_type}", extra=extra)


def log_business_event(
    logger: logging.Logger,
    event_type: str,
    user_id: str = None,
    details: Dict[str, Any] = None
):
    """Log business event"""
    extra = {
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {}
    }
    
    logger.info(f"Business event: {event_type}", extra=extra)
