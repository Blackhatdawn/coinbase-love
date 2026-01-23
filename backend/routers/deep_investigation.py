"""
Deep Investigation Endpoint

Provides a comprehensive diagnostic report of the backend system.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import psutil
import asyncio
from typing import Dict, Any

from config import settings
from database import DatabaseConnection
from dependencies import get_db
from redis_enhanced import redis_enhanced
from coincap_service import coincap_service

router = APIRouter()

async def get_system_status():
    """Gathers system metrics like CPU, memory, and disk."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }

async def get_config_status():
    """Checks the application's configuration."""
    return {
        "environment": settings.environment,
        "sentry_enabled": settings.is_sentry_available(),
        "cors_origins_configured": len(settings.get_cors_origins_list()) > 0,
        "rate_limiting_enabled": settings.rate_limit_requests_per_minute > 0,
    }

async def get_database_status(db: DatabaseConnection):
    """Checks the database connection status."""
    if not db or not db.is_connected:
        return {"status": "disconnected"}
    try:
        await asyncio.wait_for(db.health_check(), timeout=2.0)
        return {"status": "connected"}
    except asyncio.TimeoutError:
        return {"status": "timeout"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

async def get_redis_status():
    """Checks the Redis connection status."""
    try:
        # Use a simple PING command to check the connection
        await redis_enhanced.execute_lua("return redis.call('PING')", keys=[], args=[])
        return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

async def get_coincap_status():
    """Checks the status of the CoinCap service."""
    try:
        # Fetch a single asset to verify the service is responsive
        await coincap_service.get_coin_details("bitcoin")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/deep-investigation", tags=["monitoring"])
async def deep_investigation(db: DatabaseConnection = Depends(get_db)):
    """
    Performs a deep investigation of the backend, checking system status,
    configuration, and external service connections.
    """
    start_time = datetime.utcnow()

    # Run all checks concurrently
    results = await asyncio.gather(
        get_system_status(),
        get_config_status(),
        get_database_status(db),
        get_redis_status(),
        get_coincap_status(),
    )

    end_time = datetime.utcnow()
    duration_ms = (end_time - start_time).total_seconds() * 1000

    system_status, config_status, db_status, redis_status, coincap_status = results

    all_systems_go = (
        db_status["status"] == "connected" and
        redis_status["status"] == "connected" and
        coincap_status["status"] == "healthy"
    )

    return {
        "report_generated_at": start_time.isoformat(),
        "investigation_duration_ms": round(duration_ms, 2),
        "summary": {
            "all_systems_go": all_systems_go,
            "status": "HEALTHY" if all_systems_go else "DEGRADED"
        },
        "details": {
            "system": system_status,
            "configuration": config_status,
            "database": db_status,
            "redis": redis_status,
            "external_services": {
                "coincap": coincap_status,
            },
        },
    }
