"""
Phase 4 Advanced Request Management - Monitoring Router
Provides REST endpoints for all Phase 4 metrics and controls
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from request_deduplication import request_deduplicator
from smart_cache import smart_cache
from rate_limiter import rate_limiter
from connection_pool_manager import connection_pool_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/phase4", tags=["phase4-monitoring"])


@router.get(
    "/deduplication/stats",
    response_model=Dict[str, Any],
    summary="Request deduplication metrics",
    description="Returns deduplication statistics and savings"
)
async def get_deduplication_stats():
    """
    Get request deduplication metrics.
    
    Returns:
    - Dedup successes: Number of times dedup coalesced requests
    - Latency saved: Total time saved by request deduplication
    - In-flight requests: Currently pending deduplicated requests
    """
    try:
        stats = await request_deduplicator.get_stats()
        return {
            "component": "request_deduplication",
            "metrics": stats
        }
    except Exception as e:
        logger.error(f"Error fetching dedup stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.get(
    "/cache/stats",
    response_model=Dict[str, Any],
    summary="Smart cache metrics",
    description="Returns cache hit rates and efficiency metrics"
)
async def get_cache_stats():
    """
    Get smart cache statistics.
    
    Returns:
    - Cache hit rate: Percentage of requests served from cache
    - Stale serves: Times stale data was served while refreshing
    - Items cached: Current number of cached items
    """
    try:
        stats = await smart_cache.get_stats()
        return {
            "component": "smart_cache",
            "metrics": stats
        }
    except Exception as e:
        logger.error(f"Error fetching cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.get(
    "/cache/invalidate",
    summary="Invalidate cache entries",
    description="Invalidate cache by pattern"
)
async def invalidate_cache(pattern: str = None):
    """
    Invalidate cache entries matching pattern.
    
    - pattern: None = all, "prefix:*" = prefix match
    """
    try:
        await smart_cache.invalidate(pattern)
        return {
            "action": "invalidate",
            "pattern": pattern or "all",
            "message": f"Cache invalidated: {pattern or 'all'}"
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@router.get(
    "/rate-limit/stats",
    response_model=Dict[str, Any],
    summary="Rate limiting metrics",
    description="Returns rate limit enforcement statistics"
)
async def get_rate_limit_stats():
    """
    Get rate limiting statistics.
    
    Returns:
    - Rejected requests: Requests rejected by rate limits
    - Queued requests: Requests queued for later processing
    - Active limits: Number of configured user/endpoint limits
    """
    try:
        stats = await rate_limiter.get_stats()
        return {
            "component": "rate_limiter",
            "metrics": stats
        }
    except Exception as e:
        logger.error(f"Error fetching rate limit stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.post(
    "/rate-limit/user/{user_id}",
    summary="Set user rate limit",
    description="Configure rate limit for a specific user"
)
async def set_user_rate_limit(user_id: str, requests_per_minute: int):
    """
    Set rate limit for a user.
    
    Args:
    - user_id: User identifier
    - requests_per_minute: Maximum requests per minute
    """
    try:
        rate_limiter.add_user_limit(user_id, requests_per_minute)
        return {
            "user_id": user_id,
            "limit": requests_per_minute,
            "message": f"Rate limit set for {user_id}: {requests_per_minute}/min"
        }
    except Exception as e:
        logger.error(f"Error setting rate limit: {e}")
        raise HTTPException(status_code=500, detail="Failed to set rate limit")


@router.get(
    "/connections/stats",
    response_model=Dict[str, Any],
    summary="Database connection pool statistics",
    description="Returns connection pool health and metrics"
)
async def get_connection_pool_stats():
    """
    Get database connection pool statistics.
    
    Returns:
    - Pool size: Current/max connections
    - Active: Actively used connections
    - Idle: Idle connections available
    - Health: Whether pool is healthy
    """
    try:
        stats = await connection_pool_manager.get_stats()
        health = await connection_pool_manager.health_check()
        
        return {
            "component": "connection_pool",
            "statistics": stats,
            "health": health
        }
    except Exception as e:
        logger.error(f"Error fetching connection pool stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.post(
    "/connections/optimize",
    summary="Optimize connection pool",
    description="Trigger pool optimization based on usage patterns"
)
async def optimize_connection_pool():
    """
    Optimize connection pool size and settings.
    """
    try:
        await connection_pool_manager.optimize_pool()
        stats = await connection_pool_manager.get_stats()
        return {
            "action": "optimize",
            "message": "Connection pool optimized",
            "new_max_size": connection_pool_manager.max_pool_size,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error optimizing pool: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize pool")


@router.get(
    "/all-metrics",
    response_model=Dict[str, Any],
    summary="All Phase 4 metrics combined",
    description="Returns comprehensive metrics for all Phase 4 components"
)
async def get_all_phase4_metrics():
    """
    Get comprehensive metrics for all Phase 4 components.
    """
    try:
        dedup_stats = await request_deduplicator.get_stats()
        cache_stats = await smart_cache.get_stats()
        ratelimit_stats = await rate_limiter.get_stats()
        connection_stats = await connection_pool_manager.get_stats()
        connection_health = await connection_pool_manager.health_check()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_deduplication": dedup_stats,
            "smart_cache": cache_stats,
            "rate_limiting": ratelimit_stats,
            "connection_pool": {
                "statistics": connection_stats,
                "health": connection_health
            },
            "system_efficiency": {
                "cache_hit_rate": cache_stats.get("hit_rate_percentage", 0),
                "dedup_savings_seconds": dedup_stats.get("total_latency_saved_seconds", 0),
                "pool_utilization_percent": connection_stats.get("capacity_percentage", 0),
                "requests_rejected_by_limits": ratelimit_stats.get("rejected_requests", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching all metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")


@router.post(
    "/maintenance/cleanup",
    summary="Trigger system cleanup",
    description="Clean up expired resources across all Phase 4 components"
)
async def trigger_cleanup():
    """
    Trigger cleanup operations across all Phase 4 components.
    """
    try:
        dedup_cleaned = await request_deduplicator.clear_expired()
        cache_cleaned = await smart_cache.cleanup_expired()
        pool_cleaned = await connection_pool_manager.cleanup_idle_connections()
        
        return {
            "action": "cleanup",
            "results": {
                "dedup_expired_removed": dedup_cleaned,
                "cache_expired_removed": cache_cleaned,
                "idle_connections_removed": pool_cleaned
            },
            "message": f"Cleanup complete: {dedup_cleaned + cache_cleaned + pool_cleaned} items removed"
        }
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform cleanup")


# Import for datetime if not already imported
from datetime import datetime, timezone
