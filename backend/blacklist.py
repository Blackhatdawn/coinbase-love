"""
Token blacklisting module.
Uses Redis (Upstash) for fast, expiring blacklist (preferred).
Falls back to MongoDB collection if Redis unavailable.

Security Audit Fixes:
- C6: datetime.now(timezone.utc) -> datetime.now(timezone.utc)
- M5: Lazy DB access instead of module-level import
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)

# Global async Redis client (lazy init)
_redis_client: Optional[redis.Redis] = None


def _get_db():
    """Lazy DB accessor to avoid module-level circular import."""
    from dependencies import get_db
    try:
        return get_db()
    except Exception:
        return None


async def get_redis_client() -> Optional[redis.Redis]:
    """Get or create async Redis client if configured."""
    global _redis_client
    if settings.is_redis_available() and _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.upstash_redis_rest_url,
                password=settings.upstash_redis_rest_token,
                decode_responses=True
            )
            await _redis_client.ping()
            logger.info("Redis client initialized for token blacklisting")
        except Exception as e:
            logger.warning(f"Redis connection failed - falling back to MongoDB: {str(e)}")
            _redis_client = None
    return _redis_client


async def blacklist_token(token: str, expires_in: int):
    """
    H8 FIX: Add token to blacklist by jti (not full token) for efficiency.
    Uses Redis TTL or MongoDB expires_at field.
    
    This stores only the token jti (unique ID) rather than the full token,
    reducing memory usage and improving lookup performance.
    """
    # Extract jti from token to use as blacklist key
    from auth import get_token_jti
    jti = get_token_jti(token)
    if not jti:
        logger.warning("Could not extract jti from token for blacklisting")
        # Fallback: blacklist the full token
        jti = token
    
    client = await get_redis_client()
    if client:
        try:
            # H8 FIX: Store only jti, not full token
            await client.set(f"blacklist:jti:{jti}", "revoked", ex=max(expires_in, 60))
            logger.debug(f"Token jti blacklisted in Redis (expires in {expires_in}s)")
            return
        except Exception as e:
            logger.error(f"Redis blacklist failed: {str(e)}")

    db = _get_db()
    if db is not None:
        try:
            # H8 FIX: Store only jti, not full token
            await db.get_collection("blacklisted_tokens").insert_one({
                "jti": jti,
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=max(expires_in, 60))
            })
            logger.debug("Token jti blacklisted in MongoDB fallback")
        except Exception as e:
            logger.error(f"MongoDB blacklist fallback failed: {str(e)}")


async def is_token_blacklisted(token: str) -> bool:
    """
    H8 FIX: Check if token is blacklisted by jti (not full token).
    Uses Redis or MongoDB for efficient lookup.
    """
    # Extract jti from token
    from auth import get_token_jti
    jti = get_token_jti(token)
    if not jti:
        logger.warning("Could not extract jti from token for blacklist check")
        # Fallback: check full token
        jti = token
    
    client = await get_redis_client()
    if client:
        try:
            # H8 FIX: Check only jti key
            exists = await client.exists(f"blacklist:jti:{jti}")
            return bool(exists)
        except Exception as e:
            logger.error(f"Redis blacklist check failed: {str(e)}")
            return False

    db = _get_db()
    if db is not None:
        try:
            # H8 FIX: Query only jti field, not full token
            doc = await db.get_collection("blacklisted_tokens").find_one({
                "jti": jti,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            return doc is not None
        except Exception as e:
            logger.error(f"MongoDB blacklist check failed: {str(e)}")
            return False

    return False


async def cleanup_blacklisted_tokens():
    """Remove expired tokens from MongoDB fallback (Redis auto-expires)."""
    if not settings.is_redis_available():
        db = _get_db()
        if db is not None:
            try:
                await db.get_collection("blacklisted_tokens").delete_many({
                    "expires_at": {"$lt": datetime.now(timezone.utc)}
                })
                logger.info("Cleaned expired blacklisted tokens from MongoDB")
            except Exception as e:
                logger.error(f"Token cleanup failed: {str(e)}")
