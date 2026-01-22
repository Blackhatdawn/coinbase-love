"""Shared rate limit helpers with Redis support and in-memory fallback."""

from datetime import datetime
from typing import Dict, Tuple
import logging

from fastapi import HTTPException, status

from blacklist import get_redis_client

logger = logging.getLogger(__name__)

# In-memory fallback: {key: (count, window_start)}
_rate_limit_cache: Dict[str, Tuple[int, datetime]] = {}


async def enforce_rate_limit(
    key: str,
    limit: int,
    window_seconds: int = 60,
) -> None:
    """Enforce a rate limit per key."""
    client = await get_redis_client()
    if client:
        try:
            current = await client.incr(key)
            if current == 1:
                await client.expire(key, window_seconds)
            if current > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            return
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Redis rate limit failed, falling back: %s", exc)

    now = datetime.utcnow()
    count, window_start = _rate_limit_cache.get(key, (0, now))
    elapsed = (now - window_start).total_seconds()
    if elapsed >= window_seconds:
        _rate_limit_cache[key] = (1, now)
        return

    count += 1
    _rate_limit_cache[key] = (count, window_start)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
