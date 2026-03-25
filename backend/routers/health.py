"""
Health Check Endpoints for CryptoVault API.

Provides two separate endpoints:
- GET /health/live (liveness probe) - Simple fast check, no DB/Redis/external calls
- GET /health/ready (readiness probe) - Full dependency check with parallel execution

Designed for Kubernetes / Render.com health probes.
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Response

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health/live")
@router.get("/api/health/live")
async def liveness_probe():
    """
    Liveness probe - Simple fast check.
    No DB, no external calls, no Redis.
    Returns 200 if the process is alive and can handle HTTP requests.

    Use for:
    - Kubernetes livenessProbe
    - Render.com health checks
    - Load balancer health checks
    """
    return {"status": "ok"}


@router.get("/health/ready")
@router.get("/api/health/ready")
async def readiness_probe(response: Response):
    """
    Readiness probe - Full dependency check.
    Checks MongoDB, Redis, and price stream cache freshness.
    Runs dependency checks in parallel with timeouts.

    Returns:
    - 200 OK: All critical dependencies healthy
    - 503 Service Unavailable: Any critical dependency down

    Use for:
    - Kubernetes readinessProbe
    - Pre-deployment smoke tests
    - Monitoring dashboards
    """
    import dependencies
    from redis_cache import redis_cache
    from services import price_stream_service

    results = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "version": settings.app_version,
        "checks": {},
    }

    async def check_mongodb() -> dict:
        """Check MongoDB connectivity."""
        try:
            db_conn = dependencies._db_connection
            if not db_conn or not db_conn.is_connected:
                return {"status": "down", "detail": "Not connected"}
            await asyncio.wait_for(db_conn.health_check(), timeout=3.0)
            return {"status": "up"}
        except asyncio.TimeoutError:
            return {"status": "degraded", "detail": "Health check timed out"}
        except Exception as e:
            return {"status": "down", "detail": str(e)}

    async def check_redis() -> dict:
        """Check Redis connectivity."""
        try:
            if not redis_cache.use_redis:
                return {"status": "skipped", "detail": "Redis not configured, using in-memory fallback"}
            # Try a simple set/get to verify Redis is working
            test_key = "health:check:ping"
            await redis_cache.set(test_key, "pong", ttl=10)
            val = await redis_cache.get(test_key)
            if val == "pong":
                return {"status": "up"}
            return {"status": "degraded", "detail": "Set/get mismatch"}
        except Exception as e:
            return {"status": "down", "detail": str(e)}

    async def check_price_stream() -> dict:
        """Check price stream cache freshness (no external API calls)."""
        try:
            freshness = await price_stream_service.get_cache_freshness()
            healthy = await price_stream_service.health_check()
            return {
                "status": "up" if healthy else "degraded",
                "prices_cached": freshness["prices_cached"],
                "has_cached_data": freshness["has_cached_data"],
                "stream_state": freshness["stream_state"],
                "last_update": freshness["last_successful_update"],
            }
        except Exception as e:
            return {"status": "down", "detail": str(e)}

    # Run all checks in parallel with individual timeouts
    try:
        mongo_result, redis_result, price_result = await asyncio.wait_for(
            asyncio.gather(
                check_mongodb(),
                check_redis(),
                check_price_stream(),
                return_exceptions=True,
            ),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        response.status_code = 503
        results["status"] = "timeout"
        results["checks"] = {
            "mongodb": {"status": "timeout"},
            "redis": {"status": "timeout"},
            "price_stream": {"status": "timeout"},
        }
        return results

    # Handle exceptions from gather
    if isinstance(mongo_result, Exception):
        mongo_result = {"status": "down", "detail": str(mongo_result)}
    if isinstance(redis_result, Exception):
        redis_result = {"status": "down", "detail": str(redis_result)}
    if isinstance(price_result, Exception):
        price_result = {"status": "down", "detail": str(price_result)}

    results["checks"]["mongodb"] = mongo_result
    results["checks"]["redis"] = redis_result
    results["checks"]["price_stream"] = price_result

    # Determine overall status - MongoDB is critical
    if mongo_result.get("status") == "down":
        results["status"] = "unavailable"
        response.status_code = 503
    elif redis_result.get("status") == "down":
        # Redis down is degraded but not fatal (in-memory fallback exists)
        results["status"] = "degraded"
    elif price_result.get("status") == "down":
        results["status"] = "degraded"

    return results
