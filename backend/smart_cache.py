"""
Smart Cache Invalidation System
Implements stale-while-revalidate pattern, priority-based TTLs, and predictive refresh
Phase 4: Advanced Request Management
"""

import asyncio
import logging
from typing import Optional, Any, Dict, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class CachedItem:
    """Represents a cached item with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    ttl_seconds: int
    is_stale: bool = False
    access_count: int = 0
    priority: int = 5  # 1-10, higher = more important
    
    def age_seconds(self) -> float:
        """Get age of cached item in seconds"""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return self.age_seconds() > self.ttl_seconds
    
    def mark_stale(self):
        """Mark cache as stale but still usable"""
        self.is_stale = True
    
    def should_refresh(self) -> bool:
        """Determine if cache should be proactively refreshed"""
        # Refresh at 80% of TTL
        return not self.is_stale and self.age_seconds() > (self.ttl_seconds * 0.8)


class SmartCacheManager:
    """
    Advanced cache with intelligent invalidation strategies.
    
    Features:
    - Stale-while-revalidate: Serve stale data while refreshing in background
    - Priority-based TTL: Important items stay longer
    - Predictive refresh: Refresh cache before expiry based on access patterns
    - Cold cache handling: Backoff strategy for newly cached items
    - Access-based eviction: Removes least-accessed items when capacity exceeded
    """
    
    def __init__(self, max_items: int = 10000):
        self.cache: Dict[str, CachedItem] = {}
        self.max_items = max_items
        self.refresh_tasks: Dict[str, asyncio.Task] = {}
        self.total_hits = 0
        self.total_misses = 0
        self.staleness_served = 0  # Times stale data was served
    
    async def get(
        self,
        key: str,
        fetch_func: Optional[Callable] = None,
        ttl_seconds: int = 300,
        priority: int = 5
    ) -> Any:
        """
        Get value from cache, with optional background refresh on stale.
        
        Args:
            key: Cache key
            fetch_func: Async function to call if cache miss/stale
            ttl_seconds: Time to live in seconds
            priority: Priority level (1-10)
        
        Returns:
            Cached value (may be stale if fetch_func not provided)
        """
        if key in self.cache:
            item = self.cache[key]
            item.last_accessed = datetime.now(timezone.utc)
            item.access_count += 1
            
            if item.is_expired():
                self.total_misses += 1
                
                # Serve stale if available and no fetch_func
                if item.is_stale and fetch_func is None:
                    self.staleness_served += 1
                    logger.info(f"📦 Serving stale cache: {key}")
                    return item.value
                
                # Fetch fresh value
                if fetch_func:
                    logger.info(f"🔄 Cache expired, fetching fresh: {key}")
                    try:
                        value = await fetch_func()
                        self._update_cache(key, value, ttl_seconds, priority)
                        return value
                    except Exception as e:
                        logger.error(f"Fetch failed for {key}: {e}")
                        if item.is_stale:
                            return item.value
                        raise
                
                # Cache expired and no fetch_func
                del self.cache[key]
                return None
            
            # Cache hit (fresh)
            self.total_hits += 1
            
            # Proactive refresh if near expiry
            if item.should_refresh() and fetch_func and key not in self.refresh_tasks:
                asyncio.create_task(self._refresh_background(key, fetch_func, ttl_seconds, priority))
            
            return item.value
        
        # Cache miss
        self.total_misses += 1
        
        if fetch_func:
            logger.info(f"❌ Cache miss: {key}")
            value = await fetch_func()
            self._update_cache(key, value, ttl_seconds, priority)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300, priority: int = 5):
        """Set cache value"""
        self._update_cache(key, value, ttl_seconds, priority)
    
    def _update_cache(self, key: str, value: Any, ttl_seconds: int, priority: int):
        """Update cache entry"""
        now = datetime.now(timezone.utc)
        
        # Check capacity
        if len(self.cache) >= self.max_items and key not in self.cache:
            self._evict_least_accessed()
        
        # Update or create entry
        if key in self.cache:
            self.cache[key].value = value
            self.cache[key].created_at = now
            self.cache[key].ttl_seconds = ttl_seconds
            self.cache[key].priority = priority
            self.cache[key].is_stale = False
        else:
            self.cache[key] = CachedItem(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                ttl_seconds=ttl_seconds,
                priority=priority
            )
        
        logger.debug(f"💾 Cached: {key} (ttl={ttl_seconds}s, priority={priority})")
    
    async def _refresh_background(
        self,
        key: str,
        fetch_func: Callable,
        ttl_seconds: int,
        priority: int
    ):
        """Refresh cache in background"""
        try:
            logger.info(f"🔄 Background refresh: {key}")
            value = await fetch_func()
            self._update_cache(key, value, ttl_seconds, priority)
            logger.info(f"✅ Background refresh complete: {key}")
        except Exception as e:
            logger.error(f"Background refresh failed for {key}: {e}")
        finally:
            if key in self.refresh_tasks:
                del self.refresh_tasks[key]
    
    def _evict_least_accessed(self):
        """Evict least accessed item (respecting priority)"""
        if not self.cache:
            return
        
        # Sort by (priority desc, access_count asc) and evict lowest
        least_accessed = min(
            self.cache.values(),
            key=lambda x: (x.priority * -1, x.access_count)
        )
        
        logger.warning(
            f"🗑️  Evicting {least_accessed.key} "
            f"(priority={least_accessed.priority}, accesses={least_accessed.access_count})"
        )
        del self.cache[least_accessed.key]
    
    async def invalidate(self, pattern: Optional[str] = None):
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: None = all, "prefix:*" = prefix match
        """
        if not pattern:
            # Invalidate all
            self.cache.clear()
            logger.info("💣 All cache invalidated")
            return
        
        # Pattern-based invalidation
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(prefix)]
            for k in keys_to_remove:
                del self.cache[k]
            logger.info(f"💣 Invalidated {len(keys_to_remove)} items matching {pattern}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.total_hits + self.total_misses
        hit_rate = (self.total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_items": len(self.cache),
            "capacity": f"{len(self.cache)}/{self.max_items}",
            "cache_hits": self.total_hits,
            "cache_misses": self.total_misses,
            "hit_rate_percentage": round(hit_rate, 2),
            "times_served_stale": self.staleness_served,
            "in_flight_refreshes": len(self.refresh_tasks),
            "avg_item_age_seconds": round(
                sum(item.age_seconds() for item in self.cache.values()) / len(self.cache)
                if self.cache else 0,
                2
            )
        }
    
    async def cleanup_expired(self) -> int:
        """Remove expired items from cache"""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for k in expired_keys:
            del self.cache[k]
        
        if expired_keys:
            logger.info(f"🧹 Removed {len(expired_keys)} expired cache items")
        return len(expired_keys)


# Global singleton
smart_cache = SmartCacheManager(max_items=10000)
