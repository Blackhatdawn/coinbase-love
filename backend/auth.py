from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
from config import settings

# JWT settings from config (persistent across restarts)
SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

# Simple password hashing using hashlib (for demo purposes)
# In production, use a proper library like passlib with bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Simple SHA256 hash for demo
    password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return password_hash == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Simple SHA256 hash for demo
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_backup_codes(count: int = 8) -> list:
    """Generate backup codes for 2FA"""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def generate_2fa_secret() -> str:
    """Generate a secret for 2FA"""
    return secrets.token_urlsafe(32)
