"""
Cryptocurrency Prices API Endpoints
Real-time prices from Redis cache (updated by WebSocket streams)
Includes monitoring and metrics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from services import price_stream_service
from redis_cache import redis_cache
from monitoring import price_stream_metrics
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("")
async def get_all_prices() -> Dict[str, Any]:
    """
    Get all cached cryptocurrency prices.
    Prices are updated in real-time by WebSocket stream.
    
    Returns:
    {
        "prices": {
            "bitcoin": "45000.50",
            "ethereum": "2500.25",
            ...
        },
        "status": {
            "state": "connected",
            "source": "coincap",
            "last_update": "2026-01-16T05:00:00.000Z"
        }
    }
    """
    try:
        # Get all prices from service
        status = price_stream_service.get_status()
        
        return {
            "prices": price_stream_service.prices,
            "status": status,
            "count": len(price_stream_service.prices)
        }
    
    except Exception as e:
        logger.error(f"❌ Error getting prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prices")


@router.get("/{symbol}")
async def get_price(symbol: str) -> Dict[str, Any]:
    """
    Get cached price for a specific cryptocurrency symbol.
    
    Example: GET /api/prices/bitcoin
    Returns: {"symbol": "bitcoin", "price": "45000.50", "cached_at": "2026-01-16T05:00:00.000Z"}
    """
    try:
        # Try cache first (lowercase for consistency)
        cache_key = f"crypto:price:{symbol.lower()}"
        cached_price = await redis_cache.get(cache_key)
        
        if cached_price:
            return {
                "symbol": symbol.lower(),
                "price": str(cached_price),
                "source": "redis_cache"
            }
        
        # Try in-memory if not in Redis
        if symbol in price_stream_service.prices:
            return {
                "symbol": symbol,
                "price": str(price_stream_service.prices[symbol]),
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
        "source": "coincap",
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
                prices[symbol] = str(cached_price)
            elif symbol in price_stream_service.prices:
                prices[symbol] = str(price_stream_service.prices[symbol])
        
        return {
            "prices": prices,
            "requested": len(symbol_list),
            "found": len(prices)
        }
    
    except Exception as e:
        logger.error(f"❌ Error getting bulk prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prices")
