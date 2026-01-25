"""
Production Optimization Endpoints

Provides monitoring endpoints for:
1. Performance metrics
2. Cache statistics
3. Security status
4. Connection pool health
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.get("/metrics")
async def get_optimization_metrics() -> Dict[str, Any]:
    """
    Get comprehensive optimization metrics.
    """
    from performance_optimizations import response_cache, pool_monitor
    from security_hardening import anomaly_detector
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cache": {
            "status": "active",
            "statistics": response_cache.stats()
        },
        "database": {
            "connection_pool": pool_monitor.get_statistics()
        },
        "security": {
            "blocked_ips_count": len(anomaly_detector._blocked_ips),
            "monitoring": "active"
        }
    }


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get detailed cache statistics.
    """
    from performance_optimizations import response_cache
    
    stats = response_cache.stats()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cache": {
            **stats,
            "status": "healthy" if stats["hit_rate"] > 0 else "warming_up"
        }
    }


@router.post("/cache/invalidate")
async def invalidate_cache(pattern: str = None) -> Dict[str, Any]:
    """
    Invalidate cache entries.
    
    Args:
        pattern: Optional pattern to match cache keys
    """
    from performance_optimizations import response_cache
    
    count = response_cache.invalidate(pattern)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "invalidated_count": count,
        "pattern": pattern or "*"
    }


@router.get("/security/status")
async def get_security_status() -> Dict[str, Any]:
    """
    Get security monitoring status.
    """
    from security_hardening import anomaly_detector, input_sanitizer
    
    blocked_ips = anomaly_detector.get_blocked_ips()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "active",
        "blocked_ips": {
            "count": len(blocked_ips),
            "list": blocked_ips[:10]  # Return first 10 only
        },
        "features": {
            "anomaly_detection": True,
            "input_sanitization": True,
            "request_fingerprinting": True,
            "audit_logging": True
        }
    }


@router.post("/security/unblock-ip")
async def unblock_ip(ip: str) -> Dict[str, Any]:
    """
    Manually unblock an IP address.
    """
    from security_hardening import anomaly_detector, is_valid_ip
    
    if not is_valid_ip(ip):
        return {
            "success": False,
            "error": "Invalid IP address format"
        }
    
    was_blocked = ip in anomaly_detector._blocked_ips
    anomaly_detector.unblock_ip(ip)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "success": True,
        "ip": ip,
        "was_blocked": was_blocked
    }


@router.get("/database/pool")
async def get_pool_stats() -> Dict[str, Any]:
    """
    Get database connection pool statistics.
    """
    from performance_optimizations import pool_monitor
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "statistics": pool_monitor.get_statistics()
    }
