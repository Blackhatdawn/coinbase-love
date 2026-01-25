"""
Enterprise-Grade Logging System for CryptoVault Backend

Features:
- Structured JSON logging for production
- Actionable log messages with clear operator guidance
- Request correlation with unique IDs
- Performance metrics tracking
- Security event logging
- Health check aggregation (reduces noise)
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from functools import wraps
import time

from config import settings


class ActionableLogFormatter(logging.Formatter):
    """
    JSON formatter with actionable messages for operators.
    
    Each log includes:
    - timestamp: ISO format UTC
    - level: Log level
    - logger: Logger name
    - message: Human readable message
    - action_required: What operator should do (if applicable)
    - context: Additional structured data
    """
    
    # Map log levels to severity and recommended actions
    SEVERITY_MAP = {
        'DEBUG': {'severity': 'debug', 'action': None},
        'INFO': {'severity': 'info', 'action': None},
        'WARNING': {'severity': 'warning', 'action': 'monitor'},
        'ERROR': {'severity': 'error', 'action': 'investigate'},
        'CRITICAL': {'severity': 'critical', 'action': 'immediate_action_required'},
    }
    
    # Known issues with recommended fixes
    KNOWN_ISSUES = {
        'DNS resolution failed': {
            'action': 'Check network connectivity and DNS settings',
            'docs': 'https://docs.render.com/troubleshooting#dns-issues'
        },
        'rate limited': {
            'action': 'Consider upgrading API plan or implementing backoff',
            'docs': 'https://docs.coincap.io/rate-limits'
        },
        'connection refused': {
            'action': 'Verify target service is running and accessible',
            'docs': None
        },
        'timeout': {
            'action': 'Check network latency or increase timeout values',
            'docs': None
        },
        'authentication failed': {
            'action': 'Verify API keys and credentials in environment variables',
            'docs': None
        },
        'database connection': {
            'action': 'Check MONGO_URL and database accessibility',
            'docs': None
        },
        'redis connection': {
            'action': 'Verify UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN',
            'docs': None
        },
        'CSRF token missing': {
            'action': 'Client must include X-CSRF-Token header for state-changing requests',
            'docs': None
        },
    }

    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add severity info
        severity_info = self.SEVERITY_MAP.get(record.levelname, {'severity': 'unknown', 'action': None})
        
        # Check for known issues and add actionable guidance
        message_lower = record.getMessage().lower()
        for issue_key, issue_info in self.KNOWN_ISSUES.items():
            if issue_key.lower() in message_lower:
                log_entry['action_required'] = issue_info['action']
                if issue_info['docs']:
                    log_entry['documentation'] = issue_info['docs']
                break
        
        # Add any extra attributes from the log record
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'log_type'):
            log_entry['type'] = record.log_type
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            log_entry['action_required'] = 'Review exception stack trace and fix code issue'
            
        return json.dumps(log_entry)


class HealthCheckFilter(logging.Filter):
    """
    Filter to reduce health check log noise.
    Aggregates health checks and only logs periodically.
    """
    
    def __init__(self, aggregate_interval: int = 60):
        super().__init__()
        self.aggregate_interval = aggregate_interval
        self.health_check_count = 0
        self.last_health_log_time = time.time()
        
    def filter(self, record: logging.LogRecord) -> bool:
        # Check if this is a health check log
        if '/health' in record.getMessage() or '/ping' in record.getMessage():
            self.health_check_count += 1
            current_time = time.time()
            
            # Only log health checks every aggregate_interval seconds
            if current_time - self.last_health_log_time >= self.aggregate_interval:
                # Modify message to show aggregated count
                record.msg = f"Health checks received: {self.health_check_count} in last {self.aggregate_interval}s"
                self.health_check_count = 0
                self.last_health_log_time = current_time
                return True
            return False
            
        return True


class OperatorLogger:
    """
    Helper class for operator-friendly logging with actionable messages.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def startup_check(self, component: str, status: bool, details: Optional[str] = None):
        """Log startup component status"""
        if status:
            self.logger.info(
                f"✅ {component}: READY",
                extra={'log_type': 'startup_check', 'component': component, 'status': 'ready'}
            )
        else:
            self.logger.error(
                f"❌ {component}: FAILED - {details or 'Unknown error'}",
                extra={'log_type': 'startup_check', 'component': component, 'status': 'failed'}
            )
            
    def config_loaded(self, env: str, components: Dict[str, bool]):
        """Log configuration loading status"""
        self.logger.info(
            f"🔧 Configuration loaded for environment: {env}",
            extra={'log_type': 'config', 'environment': env}
        )
        for component, enabled in components.items():
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"   - {component}: {status}")
            
    def external_service_status(self, service: str, status: str, latency_ms: Optional[float] = None):
        """Log external service health"""
        msg = f"🌐 External service [{service}]: {status}"
        if latency_ms:
            msg += f" (latency: {latency_ms:.0f}ms)"
        
        if status == 'healthy':
            self.logger.info(msg, extra={'log_type': 'external_service', 'service': service})
        elif status == 'degraded':
            self.logger.warning(msg, extra={'log_type': 'external_service', 'service': service})
        else:
            self.logger.error(msg, extra={'log_type': 'external_service', 'service': service})
            
    def security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        self.logger.warning(
            f"🔒 Security event [{event_type}]: {details.get('message', 'No details')}",
            extra={'log_type': 'security', 'event_type': event_type, **details}
        )
        
    def performance_warning(self, endpoint: str, duration_ms: float, threshold_ms: float):
        """Log performance warnings when endpoints are slow"""
        self.logger.warning(
            f"⚠️ Slow response: {endpoint} took {duration_ms:.0f}ms (threshold: {threshold_ms:.0f}ms)",
            extra={
                'log_type': 'performance',
                'endpoint': endpoint,
                'duration_ms': duration_ms,
                'threshold_ms': threshold_ms
            }
        )
        
    def api_key_status(self, service: str, has_key: bool, key_preview: Optional[str] = None):
        """Log API key configuration status"""
        if has_key:
            preview = f" (key: {key_preview}...)" if key_preview else ""
            self.logger.info(f"🔑 API key configured for {service}{preview}")
        else:
            self.logger.warning(
                f"⚠️ No API key configured for {service} - service may be limited",
                extra={'log_type': 'config', 'service': service, 'action_required': f'Set {service.upper()}_API_KEY in environment'}
            )


def setup_logging(log_level: str = "INFO", json_format: bool = True):
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatting for production
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    if json_format and settings.environment == 'production':
        # Use JSON formatter for production
        console_handler.setFormatter(ActionableLogFormatter())
        # Add health check filter to reduce noise
        console_handler.addFilter(HealthCheckFilter(aggregate_interval=60))
    else:
        # Use simple formatter for development
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    
    return root_logger


def log_function_call(logger: logging.Logger):
    """Decorator to log function entry/exit with timing"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Entering {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.debug(f"Exiting {func.__name__} (took {duration:.2f}ms)")
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Error in {func.__name__}: {e} (took {duration:.2f}ms)")
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Entering {func.__name__}")
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.debug(f"Exiting {func.__name__} (took {duration:.2f}ms)")
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Error in {func.__name__}: {e} (took {duration:.2f}ms)")
                raise
                
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


# Import asyncio for decorator
import asyncio

# Create operator logger instance
operator_logger = OperatorLogger('operator')

# Export commonly used items
__all__ = [
    'setup_logging',
    'ActionableLogFormatter', 
    'HealthCheckFilter',
    'OperatorLogger',
    'operator_logger',
    'log_function_call'
]
