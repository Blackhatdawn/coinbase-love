"""
Enhanced Multi-Layer Caching System for CryptoVault.

Architecture:
- L1: In-memory cache (fastest, limited capacity, process-local)
- L2: Redis cache (fast, distributed, larger capacity)
- L3: Database query cache (slowest, persistent)

This provides optimal performance through cache hierarchy.
"""

import logging
import json
import time
from typing import Optional, Any, Dict, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio
import hashlib

logger = logging.getLogger(__name__)


class L1Cache:
    """
    Level 1 Cache: In-memory cache with LRU eviction.
    Ultra-fast but limited capacity and process-local.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        self.cache: Dict[str, tuple[Any, float, float]] = {}  # key: (value, expire_time, access_time)
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache."""
        if key in self.cache:
            value, expire_time, _ = self.cache[key]
            
            # Check if expired
            if expire_time < time.time():
                del self.cache[key]
                self.misses += 1
                return None
            
            # Update access time for LRU
            self.cache[key] = (value, expire_time, time.time())
            self.hits += 1
            return value
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in L1 cache with TTL."""
        ttl = ttl or self.default_ttl
        expire_time = time.time() + ttl
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
        
        self.cache[key] = (value, expire_time, time.time())
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from L1 cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self.cache:
            return
        
        # Find key with oldest access time
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k][2])
        del self.cache[lru_key]
        logger.debug(f"L1 evicted: {lru_key}")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "layer": "L1",
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%"
        }


class MultiLayerCache:
    """
    Multi-layer caching system with automatic fallback.
    
    Cache Hierarchy:
    1. L1 (In-Memory): ~1ms latency, 1000 items, 60s TTL
    2. L2 (Redis): ~5ms latency, 10000 items, 300s TTL  
    3. L3 (Database): ~50ms latency, unlimited, query-based
    
    On cache miss:
    - Check L1 → L2 → L3 → Database
    - Populate upper layers on fetch from lower layers
    """
    
    def __init__(self, redis_cache=None):
        # L1: In-memory cache
        self.l1 = L1Cache(max_size=1000, default_ttl=60)
        
        # L2: Redis cache (optional)
        self.l2 = redis_cache
        self.use_l2 = redis_cache is not None
        
        # Statistics
        self.l1_hits = 0
        self.l2_hits = 0
        self.l3_hits = 0
        self.total_requests = 0
        
        logger.info(f"🔄 Multi-layer cache initialized (L2={'enabled' if self.use_l2 else 'disabled'})")
    
    async def get(self, key: str, populate_callback: Optional[Callable] = None) -> Optional[Any]:
        """
        Get value from cache with automatic layer population.
        
        Args:
            key: Cache key
            populate_callback: Async function to populate cache on miss
        
        Returns:
            Cached value or None
        """
        self.total_requests += 1
        
        # Try L1 (in-memory)
        value = self.l1.get(key)
        if value is not None:
            self.l1_hits += 1
            logger.debug(f"L1 HIT: {key}")
            return value
        
        # Try L2 (Redis)
        if self.use_l2:
            value = await self.l2.get(key)
            if value is not None:
                self.l2_hits += 1
                logger.debug(f"L2 HIT: {key}")
                
                # Populate L1
                self.l1.set(key, value, ttl=60)
                return value
        
        # Try populate from callback (L3/Database)
        if populate_callback:
            try:
                value = await populate_callback()
                if value is not None:
                    self.l3_hits += 1
                    logger.debug(f"L3 HIT: {key}")
                    
                    # Populate L2 and L1
                    await self.set(key, value)
                    return value
            except Exception as e:
                logger.error(f"Cache populate callback failed: {e}")
        
        logger.debug(f"CACHE MISS: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all cache layers."""
        l1_ttl = min(ttl or 60, 60)  # L1 max 60s
        l2_ttl = ttl or 300  # L2 default 5 min
        
        # Set in L1
        self.l1.set(key, value, ttl=l1_ttl)
        
        # Set in L2 (Redis)
        if self.use_l2:
            await self.l2.set(key, value, ttl=l2_ttl)
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache layers."""
        # Delete from L1
        self.l1.delete(key)
        
        # Delete from L2
        if self.use_l2:
            await self.l2.delete(key)
        
        return True
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern."""
        # Clear L1 (no pattern support, clear all)
        if "*" in pattern:
            self.l1.clear()
        
        # TODO: Implement Redis SCAN for pattern deletion in L2
        logger.warning(f"Pattern invalidation not fully implemented: {pattern}")
    
    def get_stats(self) -> dict:
        """Get comprehensive cache statistics."""
        l1_stats = self.l1.get_stats()
        
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        overall_hit_rate = (total_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "overall_hit_rate": f"{overall_hit_rate:.2f}%",
            "l1": l1_stats,
            "l2": {
                "hits": self.l2_hits,
                "enabled": self.use_l2
            },
            "l3": {
                "hits": self.l3_hits
            },
            "hit_distribution": {
                "l1": f"{(self.l1_hits / self.total_requests * 100) if self.total_requests > 0 else 0:.2f}%",
                "l2": f"{(self.l2_hits / self.total_requests * 100) if self.total_requests > 0 else 0:.2f}%",
                "l3": f"{(self.l3_hits / self.total_requests * 100) if self.total_requests > 0 else 0:.2f}%"
            }
        }


# Cache key generators
def make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a consistent cache key from arguments."""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    key_str = ":".join(key_parts)
    
    # Hash if key is too long
    if len(key_str) > 200:
        return f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    return key_str


# Decorator for caching function results
def cached(prefix: str, ttl: int = 300):
    """
    Decorator to cache function results.
    
    Usage:
        @cached("user_profile", ttl=600)
        async def get_user_profile(user_id: str):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager from dependency injection or global
            # For now, we'll skip the actual caching in decorator
            # and let developers use cache manager directly for more control
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global cache manager instance (initialized in startup)
cache_manager: Optional[MultiLayerCache] = None


async def initialize_cache_manager(redis_cache=None):
    """Initialize the global cache manager."""
    global cache_manager
    cache_manager = MultiLayerCache(redis_cache=redis_cache)
    logger.info("✅ Cache manager initialized")
    return cache_manager


def get_cache_manager() -> Optional[MultiLayerCache]:
    """Get the global cache manager instance."""
    return cache_manager


# Specialized cache helpers for common use cases
class CacheHelpers:
    """Pre-configured cache helpers for common use cases."""
    
    @staticmethod
    async def cache_price(symbol: str, price: float, cache_mgr: MultiLayerCache):
        """Cache cryptocurrency price."""
        key = make_cache_key("price", symbol.lower())
        await cache_mgr.set(key, price, ttl=60)  # 1 minute for prices
    
    @staticmethod
    async def get_cached_price(symbol: str, cache_mgr: MultiLayerCache) -> Optional[float]:
        """Get cached cryptocurrency price."""
        key = make_cache_key("price", symbol.lower())
        return await cache_mgr.get(key)
    
    @staticmethod
    async def cache_user_profile(user_id: str, profile: dict, cache_mgr: MultiLayerCache):
        """Cache user profile."""
        key = make_cache_key("user", user_id)
        await cache_mgr.set(key, profile, ttl=600)  # 10 minutes
    
    @staticmethod
    async def get_cached_user_profile(user_id: str, cache_mgr: MultiLayerCache) -> Optional[dict]:
        """Get cached user profile."""
        key = make_cache_key("user", user_id)
        return await cache_mgr.get(key)
    
    @staticmethod
    async def cache_portfolio(user_id: str, portfolio: dict, cache_mgr: MultiLayerCache):
        """Cache user portfolio."""
        key = make_cache_key("portfolio", user_id)
        await cache_mgr.set(key, portfolio, ttl=120)  # 2 minutes
    
    @staticmethod
    async def invalidate_user_cache(user_id: str, cache_mgr: MultiLayerCache):
        """Invalidate all user-related cache."""
        await cache_mgr.delete(make_cache_key("user", user_id))
        await cache_mgr.delete(make_cache_key("portfolio", user_id))
        await cache_mgr.delete(make_cache_key("wallet", user_id))


if __name__ == "__main__":
    # Test the cache system
    async def test_cache():
        cache = MultiLayerCache()
        
        # Test basic operations
        await cache.set("test_key", "test_value", ttl=10)
        value = await cache.get("test_key")
        print(f"Retrieved: {value}")
        
        # Test cache miss with callback
        async def fetch_from_db():
            await asyncio.sleep(0.1)  # Simulate DB query
            return {"user": "john_doe"}
        
        user = await cache.get("user:123", populate_callback=fetch_from_db)
        print(f"User: {user}")
        
        # Get stats
        stats = cache.get_stats()
        print(f"Cache stats: {json.dumps(stats, indent=2)}")
    
    asyncio.run(test_cache())
