"""
Production Performance Optimizations for CryptoVault Backend

This module provides enterprise-grade performance enhancements:
1. Database query optimization with indexes and caching
2. Response caching with Redis
3. Connection pooling optimization
4. Async batch processing
5. Memory-efficient data handling
"""

import asyncio
import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================
# RESPONSE CACHING DECORATOR
# ============================================

class ResponseCache:
    """
    In-memory response cache with TTL support.
    For production, use Redis via redis_enhanced module.
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry["expires_at"]:
                self._hits += 1
                return entry["value"]
            else:
                del self._cache[key]
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """Set cache value with TTL."""
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["created_at"])
            del self._cache[oldest_key]
        
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl_seconds
        }
    
    def invalidate(self, pattern: str = None) -> int:
        """Invalidate cache entries matching pattern."""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        
        keys_to_delete = [k for k in self._cache if pattern in k]
        for k in keys_to_delete:
            del self._cache[k]
        return len(keys_to_delete)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0
        }


# Global cache instance
response_cache = ResponseCache(max_size=500)


def cached(ttl_seconds: int = 60, prefix: str = ""):
    """
    Decorator for caching function responses.
    
    Usage:
        @cached(ttl_seconds=300, prefix="crypto")
        async def get_crypto_prices():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache_prefix = prefix or func.__name__
            cache_key = response_cache._generate_key(cache_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = response_cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_prefix}")
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            response_cache.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cache miss for {cache_prefix}, cached for {ttl_seconds}s")
            
            return result
        return wrapper
    return decorator


# ============================================
# QUERY OPTIMIZATION
# ============================================

class QueryOptimizer:
    """
    MongoDB query optimization utilities.
    """
    
    @staticmethod
    def build_projection(fields: List[str], exclude_id: bool = True) -> Dict[str, int]:
        """
        Build MongoDB projection dict.
        
        Args:
            fields: List of fields to include
            exclude_id: Whether to exclude _id field
        
        Returns:
            Projection dictionary for MongoDB queries
        """
        projection = {field: 1 for field in fields}
        if exclude_id:
            projection["_id"] = 0
        return projection
    
    @staticmethod
    def paginate_query(
        skip: int = 0,
        limit: int = 50,
        max_limit: int = 100
    ) -> Dict[str, int]:
        """
        Build pagination parameters with safety limits.
        """
        return {
            "skip": max(0, skip),
            "limit": min(max(1, limit), max_limit)
        }
    
    @staticmethod
    def build_sort(
        sort_field: str = "created_at",
        sort_order: str = "desc"
    ) -> List[tuple]:
        """
        Build MongoDB sort specification.
        """
        direction = -1 if sort_order.lower() == "desc" else 1
        return [(sort_field, direction)]
    
    @staticmethod
    def optimize_text_search(query: str) -> Dict[str, Any]:
        """
        Build optimized text search query.
        """
        # Escape special regex characters
        escaped = query.replace(".", "\\.").replace("*", "\\*")
        return {
            "$regex": escaped,
            "$options": "i"  # Case-insensitive
        }


# ============================================
# BATCH PROCESSING
# ============================================

class BatchProcessor:
    """
    Efficient batch processing for bulk operations.
    """
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def process_in_batches(
        self,
        items: List[Any],
        processor: Callable[[List[Any]], Any],
        parallel: bool = False
    ) -> List[Any]:
        """
        Process items in batches.
        
        Args:
            items: List of items to process
            processor: Async function to process each batch
            parallel: Whether to process batches in parallel
        
        Returns:
            Combined results from all batches
        """
        results = []
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        if parallel:
            # Process batches in parallel
            batch_results = await asyncio.gather(
                *[processor(batch) for batch in batches],
                return_exceptions=True
            )
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                else:
                    results.extend(result if isinstance(result, list) else [result])
        else:
            # Process batches sequentially
            for batch in batches:
                result = await processor(batch)
                results.extend(result if isinstance(result, list) else [result])
        
        return results


# ============================================
# CONNECTION POOL MONITOR
# ============================================

class ConnectionPoolMonitor:
    """
    Monitor and optimize database connection pools.
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = {
            "query_times": [],
            "connection_wait_times": [],
            "pool_sizes": []
        }
        self._max_samples = 1000
    
    def record_query_time(self, duration_ms: float):
        """Record query execution time."""
        self._metrics["query_times"].append(duration_ms)
        if len(self._metrics["query_times"]) > self._max_samples:
            self._metrics["query_times"] = self._metrics["query_times"][-self._max_samples:]
    
    def record_connection_wait(self, duration_ms: float):
        """Record time waiting for connection."""
        self._metrics["connection_wait_times"].append(duration_ms)
        if len(self._metrics["connection_wait_times"]) > self._max_samples:
            self._metrics["connection_wait_times"] = self._metrics["connection_wait_times"][-self._max_samples:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        def calc_stats(values: List[float]) -> Dict[str, float]:
            if not values:
                return {"avg": 0, "min": 0, "max": 0, "p95": 0}
            sorted_vals = sorted(values)
            return {
                "avg": round(sum(values) / len(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "p95": round(sorted_vals[int(len(sorted_vals) * 0.95)] if len(sorted_vals) > 1 else sorted_vals[0], 2)
            }
        
        return {
            "query_times_ms": calc_stats(self._metrics["query_times"]),
            "connection_wait_ms": calc_stats(self._metrics["connection_wait_times"]),
            "sample_count": len(self._metrics["query_times"])
        }


# Global monitor instance
pool_monitor = ConnectionPoolMonitor()


# ============================================
# ASYNC UTILITIES
# ============================================

async def run_with_timeout(
    coro,
    timeout_seconds: float,
    default: Any = None
) -> Any:
    """
    Run coroutine with timeout, returning default on timeout.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout_seconds}s")
        return default


async def gather_with_concurrency(
    limit: int,
    *coros
) -> List[Any]:
    """
    Run coroutines with concurrency limit.
    
    Args:
        limit: Maximum concurrent coroutines
        *coros: Coroutines to execute
    
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(
        *[limited_coro(c) for c in coros],
        return_exceptions=True
    )


# ============================================
# DATA SERIALIZATION OPTIMIZATION
# ============================================

class FastJSONEncoder(json.JSONEncoder):
    """
    Optimized JSON encoder for common types.
    """
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


def fast_json_dumps(data: Any) -> str:
    """Fast JSON serialization with common type handling."""
    return json.dumps(data, cls=FastJSONEncoder, separators=(',', ':'))


def fast_json_loads(data: str) -> Any:
    """Fast JSON deserialization."""
    return json.loads(data)


# ============================================
# MEMORY OPTIMIZATION
# ============================================

class StreamingResponse:
    """
    Memory-efficient streaming for large responses.
    """
    
    @staticmethod
    async def stream_cursor(cursor, batch_size: int = 100):
        """
        Stream MongoDB cursor results.
        
        Yields batches of documents to avoid loading all into memory.
        """
        batch = []
        async for doc in cursor:
            # Convert ObjectId to string
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            batch.append(doc)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        if batch:
            yield batch


# ============================================
# EXPORTS
# ============================================

__all__ = [
    'response_cache',
    'cached',
    'QueryOptimizer',
    'BatchProcessor',
    'pool_monitor',
    'ConnectionPoolMonitor',
    'run_with_timeout',
    'gather_with_concurrency',
    'fast_json_dumps',
    'fast_json_loads',
    'FastJSONEncoder',
    'StreamingResponse'
]
