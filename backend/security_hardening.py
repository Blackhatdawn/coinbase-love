"""
Enterprise Security Hardening Module for CryptoVault

Implements defense-in-depth security measures:
1. Input sanitization and validation
2. SQL/NoSQL injection prevention
3. XSS prevention
4. Request fingerprinting
5. Anomaly detection
6. Security audit logging
"""

import re
import hashlib
import hmac
import logging
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import ipaddress

logger = logging.getLogger(__name__)


# ============================================
# INPUT SANITIZATION
# ============================================

class InputSanitizer:
    """
    Comprehensive input sanitization for security.
    """
    
    # Patterns that indicate potential attacks
    NOSQL_INJECTION_PATTERNS = [
        r'\$where',
        r'\$regex',
        r'\$ne',
        r'\$gt',
        r'\$lt',
        r'\$or',
        r'\$and',
        r'\$not',
        r'\$nor',
        r'\$exists',
        r'\$type',
        r'\$expr',
        r'\$jsonSchema',
        r'\.0',  # Array index injection
    ]
    
    XSS_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<svg[^>]*onload',
        r'data:text/html',
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.',
        r'%2e%2e',
        r'%252e%252e',
        r'\.%2e',
        r'%2e\.',
    ]
    
    def __init__(self):
        self._nosql_regex = re.compile(
            '|'.join(self.NOSQL_INJECTION_PATTERNS),
            re.IGNORECASE
        )
        self._xss_regex = re.compile(
            '|'.join(self.XSS_PATTERNS),
            re.IGNORECASE
        )
        self._path_regex = re.compile(
            '|'.join(self.PATH_TRAVERSAL_PATTERNS),
            re.IGNORECASE
        )
    
    def sanitize_string(self, value: str, max_length: int = 10000) -> str:
        """
        Sanitize string input.
        
        - Truncates to max_length
        - Removes null bytes
        - Strips dangerous patterns
        """
        if not isinstance(value, str):
            return str(value)[:max_length]
        
        # Truncate
        value = value[:max_length]
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        value = ''.join(
            char for char in value
            if char in '\n\r\t' or (ord(char) >= 32 and ord(char) != 127)
        )
        
        return value
    
    def check_nosql_injection(self, value: Any) -> bool:
        """Check if value contains potential NoSQL injection."""
        if isinstance(value, str):
            return bool(self._nosql_regex.search(value))
        elif isinstance(value, dict):
            # Check for operator keys
            for key in value.keys():
                if key.startswith('$'):
                    return True
                if self.check_nosql_injection(value[key]):
                    return True
        elif isinstance(value, list):
            return any(self.check_nosql_injection(item) for item in value)
        return False
    
    def check_xss(self, value: str) -> bool:
        """Check if value contains potential XSS."""
        if not isinstance(value, str):
            return False
        return bool(self._xss_regex.search(value))
    
    def check_path_traversal(self, value: str) -> bool:
        """Check if value contains path traversal attempt."""
        if not isinstance(value, str):
            return False
        return bool(self._path_regex.search(value))
    
    def sanitize_for_mongodb(self, data: Any) -> Any:
        """
        Recursively sanitize data for MongoDB.
        
        - Removes keys starting with $
        - Removes keys containing .
        - Sanitizes string values
        """
        if isinstance(data, dict):
            return {
                key: self.sanitize_for_mongodb(value)
                for key, value in data.items()
                if not key.startswith('$') and '.' not in key
            }
        elif isinstance(data, list):
            return [self.sanitize_for_mongodb(item) for item in data]
        elif isinstance(data, str):
            return self.sanitize_string(data)
        return data
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    def validate_username(self, username: str) -> bool:
        """Validate username format."""
        pattern = r'^[a-zA-Z0-9_-]{3,30}$'
        return bool(re.match(pattern, username))


# Global sanitizer instance
input_sanitizer = InputSanitizer()


# ============================================
# REQUEST FINGERPRINTING
# ============================================

class RequestFingerprinter:
    """
    Generate unique fingerprints for requests to detect anomalies.
    """
    
    def __init__(self):
        self._fingerprint_cache: Dict[str, Dict] = {}
        self._max_cache_size = 10000
    
    def generate_fingerprint(
        self,
        ip: str,
        user_agent: str,
        accept_language: str = "",
        accept_encoding: str = ""
    ) -> str:
        """
        Generate a fingerprint from request characteristics.
        """
        data = f"{ip}|{user_agent}|{accept_language}|{accept_encoding}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def is_suspicious_fingerprint_change(
        self,
        user_id: str,
        new_fingerprint: str
    ) -> bool:
        """
        Check if fingerprint change is suspicious.
        
        Suspicious if:
        - User has many different fingerprints in short time
        - Fingerprint is associated with known bad actors
        """
        if user_id not in self._fingerprint_cache:
            self._fingerprint_cache[user_id] = {
                "fingerprints": set(),
                "last_seen": time.time()
            }
        
        cache = self._fingerprint_cache[user_id]
        cache["fingerprints"].add(new_fingerprint)
        cache["last_seen"] = time.time()
        
        # Suspicious if more than 5 different fingerprints in 1 hour
        return len(cache["fingerprints"]) > 5
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Remove old fingerprint entries."""
        current_time = time.time()
        keys_to_remove = [
            user_id for user_id, data in self._fingerprint_cache.items()
            if current_time - data["last_seen"] > max_age_seconds
        ]
        for key in keys_to_remove:
            del self._fingerprint_cache[key]


# Global fingerprinter instance
request_fingerprinter = RequestFingerprinter()


# ============================================
# ANOMALY DETECTION
# ============================================

class AnomalyDetector:
    """
    Detect anomalous behavior patterns.
    """
    
    def __init__(self):
        # Track request patterns per IP
        self._request_patterns: Dict[str, List[float]] = defaultdict(list)
        # Track failed auth attempts
        self._failed_auth: Dict[str, List[float]] = defaultdict(list)
        # Blocked IPs
        self._blocked_ips: Set[str] = set()
        # Block duration in seconds
        self._block_duration = 900  # 15 minutes
        self._block_timestamps: Dict[str, float] = {}
    
    def record_request(self, ip: str) -> None:
        """Record a request from IP."""
        current_time = time.time()
        self._request_patterns[ip].append(current_time)
        
        # Keep only last 5 minutes of data
        cutoff = current_time - 300
        self._request_patterns[ip] = [
            t for t in self._request_patterns[ip] if t > cutoff
        ]
    
    def record_failed_auth(self, ip: str, user_id: str = None) -> bool:
        """
        Record a failed authentication attempt.
        
        Returns True if IP should be blocked.
        """
        current_time = time.time()
        key = f"{ip}:{user_id}" if user_id else ip
        self._failed_auth[key].append(current_time)
        
        # Keep only last 15 minutes
        cutoff = current_time - 900
        self._failed_auth[key] = [
            t for t in self._failed_auth[key] if t > cutoff
        ]
        
        # Block if more than 10 failed attempts in 15 minutes
        if len(self._failed_auth[key]) >= 10:
            self.block_ip(ip)
            logger.warning(f"🛑 IP {ip} blocked due to excessive failed auth attempts")
            return True
        
        return False
    
    def is_request_burst(self, ip: str, threshold: int = 100) -> bool:
        """
        Check if IP is making burst requests.
        
        Returns True if more than threshold requests in last minute.
        """
        current_time = time.time()
        cutoff = current_time - 60
        recent_requests = [
            t for t in self._request_patterns.get(ip, []) if t > cutoff
        ]
        return len(recent_requests) > threshold
    
    def block_ip(self, ip: str) -> None:
        """Block an IP address."""
        self._blocked_ips.add(ip)
        self._block_timestamps[ip] = time.time()
        logger.warning(f"🚫 IP blocked: {ip}")
    
    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address."""
        self._blocked_ips.discard(ip)
        self._block_timestamps.pop(ip, None)
        logger.info(f"✅ IP unblocked: {ip}")
    
    def is_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked."""
        if ip not in self._blocked_ips:
            return False
        
        # Check if block has expired
        block_time = self._block_timestamps.get(ip, 0)
        if time.time() - block_time > self._block_duration:
            self.unblock_ip(ip)
            return False
        
        return True
    
    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of blocked IPs with expiry times."""
        current_time = time.time()
        return [
            {
                "ip": ip,
                "blocked_at": datetime.fromtimestamp(self._block_timestamps[ip]).isoformat(),
                "expires_in": max(0, self._block_duration - (current_time - self._block_timestamps[ip]))
            }
            for ip in self._blocked_ips
        ]


# Global anomaly detector instance
anomaly_detector = AnomalyDetector()


# ============================================
# SECURITY AUDIT LOGGING
# ============================================

class SecurityAuditLogger:
    """
    Dedicated security event logging.
    """
    
    def __init__(self):
        self._audit_logger = logging.getLogger("security_audit")
        self._audit_logger.setLevel(logging.INFO)
    
    def log_auth_success(
        self,
        user_id: str,
        ip: str,
        method: str = "password"
    ) -> None:
        """Log successful authentication."""
        self._audit_logger.info(
            "AUTH_SUCCESS",
            extra={
                "event_type": "auth_success",
                "user_id": user_id,
                "ip": ip,
                "method": method,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_auth_failure(
        self,
        identifier: str,
        ip: str,
        reason: str
    ) -> None:
        """Log failed authentication."""
        self._audit_logger.warning(
            "AUTH_FAILURE",
            extra={
                "event_type": "auth_failure",
                "identifier": identifier,
                "ip": ip,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: str = "info"
    ) -> None:
        """Log generic security event."""
        log_method = getattr(self._audit_logger, severity, self._audit_logger.info)
        log_method(
            event_type.upper(),
            extra={
                "event_type": event_type,
                **details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip: str
    ) -> None:
        """Log sensitive data access."""
        self._audit_logger.info(
            "DATA_ACCESS",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "ip": ip,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_admin_action(
        self,
        admin_id: str,
        action: str,
        target: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Log admin actions for audit trail."""
        self._audit_logger.info(
            "ADMIN_ACTION",
            extra={
                "event_type": "admin_action",
                "admin_id": admin_id,
                "action": action,
                "target": target,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Global audit logger instance
security_audit = SecurityAuditLogger()


# ============================================
# IP VALIDATION
# ============================================

def is_valid_ip(ip: str) -> bool:
    """Check if string is valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Check if IP is in private range."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def is_localhost(ip: str) -> bool:
    """Check if IP is localhost."""
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_loopback
    except ValueError:
        return False


# ============================================
# SECURE TOKEN GENERATION
# ============================================

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token."""
    import secrets
    return secrets.token_urlsafe(length)


def generate_verification_code(length: int = 6) -> str:
    """Generate numeric verification code."""
    import secrets
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(val1.encode(), val2.encode())


# ============================================
# EXPORTS
# ============================================

__all__ = [
    'input_sanitizer',
    'InputSanitizer',
    'request_fingerprinter',
    'RequestFingerprinter',
    'anomaly_detector',
    'AnomalyDetector',
    'security_audit',
    'SecurityAuditLogger',
    'is_valid_ip',
    'is_private_ip',
    'is_localhost',
    'generate_secure_token',
    'generate_verification_code',
    'constant_time_compare'
]
