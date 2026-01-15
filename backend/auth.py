"""
Authentication utilities: JWT tokens, password hashing, 2FA with TOTP.
Production-ready with bcrypt enforcement and pyotp for TOTP verification.
"""

from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets
import bcrypt
import logging
import pyotp  # Added for TOTP verification
from fastapi import Request
from .config import settings

logger = logging.getLogger(__name__)

# JWT settings
SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

# Enforce bcrypt
try:
    import bcrypt
    logger.info("✅ Using bcrypt for password hashing (production-ready)")
except ImportError as e:
    logger.critical("❌ Bcrypt not installed – install with 'pip install bcrypt'")
    raise RuntimeError("Bcrypt required for secure password hashing") from e

# Enforce pyotp for TOTP
try:
    import pyotp
    logger.info("✅ pyotp available for TOTP 2FA verification")
except ImportError as e:
    logger.critical("❌ pyotp not installed – install with 'pip install pyotp'")
    raise RuntimeError("pyotp required for TOTP 2FA") from e

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash with timing attack protection."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        )
    except Exception:
        # Always return False on error to prevent timing attacks
        # Use constant-time comparison even in error cases
        bcrypt.checkpw(b"dummy", bcrypt.gensalt())
        return False

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt (rounds=12)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[Dict]:
    """Decode and verify JWT, return payload or None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        logger.debug(f"Invalid token: {str(e)}")
        return None

def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate one-time backup codes for 2FA."""
    return [secrets.token_hex(4).upper() for _ in range(count)]

def generate_2fa_secret() -> str:
    """Generate base32 secret for TOTP 2FA."""
    return pyotp.random_base32()  # Proper base32 secret (pyotp recommended)

def verify_2fa_code(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify TOTP code using pyotp.
    Window allows for clock drift (default ±30 seconds).
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=window)

def generate_device_fingerprint(request: Request) -> str:
    """Generate a device fingerprint for suspicious login detection."""
    import hashlib
    
    # Collect various request attributes
    ip = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    accept_encoding = request.headers.get("accept-encoding", "")
    
    # Create a fingerprint hash
    fingerprint_data = f"{ip}:{user_agent}:{accept_language}:{accept_encoding}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()
