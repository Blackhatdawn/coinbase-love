"""
Cryptocurrency Prices API Endpoints
Real-time prices from Redis cache (updated by WebSocket streams)
Includes monitoring and metrics endpoints
Phase 2: Response caching and request retry logic
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from services import price_stream_service
from redis_cache import redis_cache
from monitoring import price_stream_metrics
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from dependencies import get_current_user_id, get_db

# Phase 2 Performance Optimization
from cache_decorator import cached_endpoint, CACHE_PRICES, CACHE_MARKET_DATA, get_cache_headers
from request_retry import with_retry, RETRY_API
from performance_monitoring import performance_metrics, RequestTimer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("")
@cached_endpoint(config=CACHE_MARKET_DATA)
@with_retry(config=RETRY_API)
async def get_all_prices(response: Response) -> Dict[str, Any]:
    """
    Get all cached cryptocurrency prices (Phase 2: Cached & Retried).
    Prices are updated in real-time by WebSocket stream.
    Uses 300s cache with 4-attempt retry logic.
    
    Returns:
    {
        "prices": {
            "bitcoin": "45000.50",
            "ethereum": "2500.25",
            ...
        },
        "status": {
            "state": "connected",
            "source": "coingecko",
            "last_update": "2026-01-16T05:00:00.000Z"
        }
    }
    """
    try:
        # Phase 2: Add cache headers for CDN/browser caching (300 seconds for market data)
        response.headers.update(get_cache_headers(ttl_seconds=300))
        
        # Get all prices from service
        async with RequestTimer("get-all-prices"):
            status = price_stream_service.get_status()
            
            # Record API timing
            performance_metrics.record_api_timing(
                endpoint="/prices",
                method="GET",
                response_time_ms=0,  # Populated by RequestTimer context
                status_code=200,
            )
            
            return {
                "prices": price_stream_service.prices,
                "status": status,
                "count": len(price_stream_service.prices)
            }
    
    except Exception as e:
        logger.error(f"❌ Error getting prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prices")


@router.get("/{symbol}")
@cached_endpoint(config=CACHE_PRICES)
@with_retry(config=RETRY_API)
async def get_price(symbol: str, response: Response) -> Dict[str, Any]:
    """
    Get cached price for a specific cryptocurrency symbol (Phase 2: Cached & Retried).
    Uses 60s cache with 4-attempt retry logic.
    
    Example: GET /api/prices/bitcoin
    Returns: {"symbol": "bitcoin", "price": "45000.50", "cached_at": "2026-01-16T05:00:00.000Z"}
    """
    try:
        # Phase 2: Add cache headers
        response.headers.update(get_cache_headers(ttl_seconds=60))
        
        async with RequestTimer(f"get-price:{symbol}"):
            # Try cache first (lowercase for consistency)
            cache_key = f"crypto:price:{symbol.lower()}"
            cached_price = await redis_cache.get(cache_key)
            
            if cached_price:
                price_value = cached_price.get("price") if isinstance(cached_price, dict) else cached_price
                performance_metrics.record_api_timing(
                    endpoint="/prices/{symbol}",
                    method="GET",
                    response_time_ms=0,  # Populated by RequestTimer
                    status_code=200,
                )
                return {
                    "symbol": symbol.lower(),
                    "price": str(price_value),
                    "source": "redis_cache"
                }
            
            # Try in-memory if not in Redis
            normalized = symbol.lower()
            if normalized in price_stream_service.prices:
                performance_metrics.record_api_timing(
                    endpoint="/prices/{symbol}",
                    method="GET",
                    response_time_ms=0,
                    status_code=200,
                )
                return {
                    "symbol": normalized,
                    "price": str(price_stream_service.prices[normalized]),
                    "source": "memory_cache"
                }
            
            # Price not found
            raise HTTPException(
                status_code=404,
                detail=f"Price for {symbol} not available. Service may be initializing."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting price for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve price")


@router.get("/status/health")
async def health_check() -> Dict[str, Any]:
    """
    Get health status of the price stream service.
    
    Returns:
    {
        "healthy": true,
        "state": "connected",
        "source": "coingecko",
        "prices_cached": 1200,
        "last_update": "2026-01-16T05:00:00.000Z"
    }
    """
    try:
        status = price_stream_service.get_status()
        is_healthy = await price_stream_service.health_check()
        
        return {
            "healthy": is_healthy,
            "state": status["state"],
            "source": status["source"],
            "prices_cached": status["prices_cached"],
            "last_update": status["last_update"],
            "last_successful_update": status["last_successful_update"],
            "reconnect_attempt": status["reconnect_attempt"]
        }
    
    except Exception as e:
        logger.error(f"❌ Error getting health status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")


@router.get("/bulk/{symbols}")
async def get_bulk_prices(symbols: str) -> Dict[str, Any]:
    """
    Get prices for multiple symbols at once.

    Example: GET /api/prices/bulk/bitcoin,ethereum,solana
    Returns: {"prices": {"bitcoin": "45000.50", "ethereum": "2500.25", "solana": "180.50"}}
    """
    try:
        symbol_list = [s.strip().lower() for s in symbols.split(",")]
        prices = {}

        for symbol in symbol_list:
            # Try cache first
            cache_key = f"crypto:price:{symbol}"
            cached_price = await redis_cache.get(cache_key)

            if cached_price:
                price_value = cached_price.get("price") if isinstance(cached_price, dict) else cached_price
                prices[symbol] = str(price_value)
                price_stream_metrics.record_cache_hit()
            elif symbol in price_stream_service.prices:
                prices[symbol] = str(price_stream_service.prices[symbol])
            else:
                price_stream_metrics.record_cache_miss()

        return {
            "prices": prices,
            "requested": len(symbol_list),
            "found": len(prices)
        }

    except Exception as e:
        logger.error(f"❌ Error getting bulk prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prices")


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get real-time metrics for the price stream service.

    Returns comprehensive statistics including:
    - Updates per second
    - Connection state and reconnect attempts
    - Recent errors
    - Cache hit rate
    - Message processing performance
    """
    try:
        metrics = price_stream_metrics.get_summary()

        return {
            "metrics": metrics,
            "service_status": price_stream_service.get_status(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.post("/metrics/reset")
async def reset_metrics(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
) -> Dict[str, str]:
    """
    Reset all metrics counters.

    ⚠️ Admin-only endpoint: Used for internal monitoring purposes.
    Resets price stream metrics including cache hit rates, update frequencies, etc.

    Note: Not called by frontend UI - used for server-side monitoring/debugging.
    """
    # Check if user is admin
    users_collection = db.get_collection("users")
    user = await users_collection.find_one({"id": user_id})

    if not user or not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        price_stream_metrics.reset()
        logger.info(f"🔄 Metrics reset by admin user: {user_id}")
        return {
            "status": "success",
            "message": "Metrics counters have been reset",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error resetting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset metrics")
