"""
Redis Caching Service for CryptoVault.

Supports two Redis backends:
1. Standard Redis (redis:// URL) via async redis-py client — for Redis Cloud, local Redis, etc.
2. Upstash Redis REST API — for serverless environments.

Falls back to in-memory cache if Redis is unavailable.
Auto-disables on repeated failures to prevent log spam.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from config import settings

logger = logging.getLogger(__name__)

# Detect which Redis backend to use
_REDIS_STANDARD_URL = settings.redis_url  # redis://...
_UPSTASH_URL = settings.upstash_redis_rest_url
_UPSTASH_TOKEN = settings.upstash_redis_rest_token

_USE_STANDARD = bool(_REDIS_STANDARD_URL)
_USE_UPSTASH = bool(_UPSTASH_URL and _UPSTASH_TOKEN) and not _USE_STANDARD


class RedisCache:
    """
    Async Redis cache with automatic fallback to in-memory.
    Prefers standard redis:// connection, then Upstash REST, then memory.
    """

    def __init__(self):
        self.use_redis = settings.is_redis_available()
        self._client = None  # async redis.Redis client (lazy init)
        self._consecutive_failures = 0
        self._max_failures = 5
        self._initialized = False

        # Upstash fallback
        self._upstash_url = _UPSTASH_URL
        self._upstash_token = _UPSTASH_TOKEN

        # In-memory fallback
        self.memory_cache: Dict[str, tuple] = {}

        # TTL defaults
        self.DEFAULT_TTL = 300
        self.PRICE_TTL = 60
        self.SESSION_TTL = 3600

        mode = "standard Redis" if _USE_STANDARD else "Upstash REST" if _USE_UPSTASH else "in-memory only"
        logger.info("Redis Cache initialized (mode=%s, redis_available=%s)", mode, self.use_redis)

    async def _get_client(self):
        """Lazy-init the async redis client for standard redis:// connections."""
        if self._client is not None:
            return self._client
        if not _USE_STANDARD:
            return None
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                _REDIS_STANDARD_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Quick connectivity check
            await self._client.ping()
            self._initialized = True
            logger.info("Connected to Redis at %s", _REDIS_STANDARD_URL.split("@")[-1] if "@" in _REDIS_STANDARD_URL else _REDIS_STANDARD_URL)
            return self._client
        except Exception as exc:
            logger.warning("Redis connection failed: %s. Using in-memory fallback.", exc)
            self._client = None
            self.use_redis = False
            return None

    def _record_failure(self):
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._max_failures and self.use_redis:
            logger.warning("Redis disabled after %d consecutive failures. Using in-memory cache.", self._consecutive_failures)
            self.use_redis = False

    def _record_success(self):
        self._consecutive_failures = 0

    # ==================================================
    # PUBLIC API
    # ==================================================

    async def get(self, key: str) -> Optional[Any]:
        if self.use_redis:
            if _USE_STANDARD:
                return await self._std_get(key)
            if _USE_UPSTASH:
                return await self._upstash_get(key)
        return self._mem_get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if self.use_redis:
            if _USE_STANDARD:
                return await self._std_set(key, value, ttl or self.DEFAULT_TTL)
            if _USE_UPSTASH:
                return await self._upstash_set(key, value, ttl or self.DEFAULT_TTL)
        return self._mem_set(key, value, ttl or self.DEFAULT_TTL)

    async def delete(self, key: str) -> bool:
        if self.use_redis:
            if _USE_STANDARD:
                return await self._std_delete(key)
            if _USE_UPSTASH:
                return await self._upstash_delete(key)
        return self._mem_delete(key)

    async def exists(self, key: str) -> bool:
        return (await self.get(key)) is not None

    async def increment(self, key: str, amount: int = 1) -> int:
        if self.use_redis:
            if _USE_STANDARD:
                return await self._std_incr(key, amount)
            if _USE_UPSTASH:
                return await self._upstash_incr(key, amount)
        return self._mem_incr(key, amount)

    async def set_with_expiry(self, key: str, value: Any, seconds: int) -> bool:
        return await self.set(key, value, seconds)

    # ==================================================
    # STANDARD REDIS (redis-py async) OPERATIONS
    # ==================================================

    async def _std_get(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            if not client:
                return self._mem_get(key)
            result = await client.get(key)
            if result is None:
                return None
            self._record_success()
            try:
                return json.loads(result)
            except (json.JSONDecodeError, TypeError):
                return result
        except Exception:
            self._record_failure()
            return self._mem_get(key)

    async def _std_set(self, key: str, value: Any, ttl: int) -> bool:
        try:
            client = await self._get_client()
            if not client:
                return self._mem_set(key, value, ttl)
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await client.setex(key, ttl, serialized)
            self._record_success()
            return True
        except Exception:
            self._record_failure()
            return self._mem_set(key, value, ttl)

    async def _std_delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            if not client:
                return self._mem_delete(key)
            await client.delete(key)
            self._record_success()
            return True
        except Exception:
            self._record_failure()
            return self._mem_delete(key)

    async def _std_incr(self, key: str, amount: int) -> int:
        try:
            client = await self._get_client()
            if not client:
                return self._mem_incr(key, amount)
            result = await client.incrby(key, amount)
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            return self._mem_incr(key, amount)

    # ==================================================
    # UPSTASH REST API OPERATIONS (kept for backward compat)
    # ==================================================

    async def _upstash_get(self, key: str) -> Optional[Any]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{self._upstash_url}/get/{key}",
                    headers={"Authorization": f"Bearer {self._upstash_token}"},
                )
                if resp.status_code == 200:
                    self._record_success()
                    result = resp.json().get("result")
                    if result is None:
                        return None
                    try:
                        parsed = json.loads(result)
                        return json.loads(parsed) if isinstance(parsed, str) else parsed
                    except (json.JSONDecodeError, TypeError):
                        return result
                self._record_failure()
                return self._mem_get(key)
        except Exception:
            self._record_failure()
            return self._mem_get(key)

    async def _upstash_set(self, key: str, value: Any, ttl: int) -> bool:
        try:
            import httpx
            serialized = json.dumps(value) if not isinstance(value, str) else value
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    self._upstash_url,
                    headers={"Authorization": f"Bearer {self._upstash_token}", "Content-Type": "application/json"},
                    json=["SETEX", key, str(ttl), serialized],
                )
                if resp.status_code == 200:
                    self._record_success()
                    return True
                self._record_failure()
                return self._mem_set(key, value, ttl)
        except Exception:
            self._record_failure()
            return self._mem_set(key, value, ttl)

    async def _upstash_delete(self, key: str) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{self._upstash_url}/del/{key}",
                    headers={"Authorization": f"Bearer {self._upstash_token}"},
                )
                return resp.status_code == 200
        except Exception:
            return self._mem_delete(key)

    async def _upstash_incr(self, key: str, amount: int) -> int:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{self._upstash_url}/incrby/{key}/{amount}",
                    headers={"Authorization": f"Bearer {self._upstash_token}"},
                )
                if resp.status_code == 200:
                    return resp.json().get("result", 0)
                return 0
        except Exception:
            return self._mem_incr(key, amount)

    # ==================================================
    # IN-MEMORY FALLBACK
    # ==================================================

    def _mem_get(self, key: str) -> Optional[Any]:
        if key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            if time.time() < expiry:
                return value
            del self.memory_cache[key]
        return None

    def _mem_set(self, key: str, value: Any, ttl: int) -> bool:
        self.memory_cache[key] = (value, time.time() + ttl)
        if len(self.memory_cache) > 1000:
            self._cleanup_memory()
        return True

    def _mem_delete(self, key: str) -> bool:
        if key in self.memory_cache:
            del self.memory_cache[key]
            return True
        return False

    def _mem_incr(self, key: str, amount: int) -> int:
        current = self._mem_get(key) or 0
        try:
            new_value = int(current) + amount
        except (ValueError, TypeError):
            new_value = amount
        self._mem_set(key, new_value, self.DEFAULT_TTL)
        return new_value

    def _cleanup_memory(self):
        now = time.time()
        expired = [k for k, (_, exp) in self.memory_cache.items() if exp < now]
        for k in expired:
            del self.memory_cache[k]

    # ==================================================
    # HELPER METHODS
    # ==================================================

    async def cache_prices(self, prices: list) -> bool:
        return await self.set("crypto:prices", prices, self.PRICE_TTL)

    async def get_cached_prices(self) -> Optional[list]:
        return await self.get("crypto:prices")

    async def cache_coin_details(self, coin_id: str, data: dict) -> bool:
        return await self.set(f"crypto:coin:{coin_id}", data, self.DEFAULT_TTL)

    async def get_cached_coin_details(self, coin_id: str) -> Optional[dict]:
        return await self.get(f"crypto:coin:{coin_id}")

    async def rate_limit_check(self, identifier: str, limit: int, window: int) -> bool:
        key = f"ratelimit:{identifier}"
        current = await self.get(key) or 0
        if int(current) >= limit:
            return False
        await self.increment(key)
        if int(current) == 0:
            await self.set_with_expiry(key, 1, window)
        return True


# Global cache instance
redis_cache = RedisCache()
