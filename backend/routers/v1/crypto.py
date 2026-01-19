"""Cryptocurrency market data endpoints with multi-source support."""

from fastapi import APIRouter, HTTPException
import logging

from multi_source_crypto_service import multi_source_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crypto", tags=["cryptocurrency"])


@router.get("")
async def get_all_cryptocurrencies():
    """
    Get all cryptocurrency prices from multiple sources.
    Primary: CoinPaprika → Secondary: CoinMarketCap → Fallback: CoinGecko
    """
    try:
        prices = await multi_source_service.get_prices()
        return {"cryptocurrencies": prices}
    except Exception as e:
        logger.error(f"❌ Error fetching cryptocurrencies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch cryptocurrency prices")


@router.get("/{coin_id}")
async def get_cryptocurrency(coin_id: str):
    """
    Get specific cryptocurrency details from multiple sources.
    Primary: CoinPaprika → Secondary: CoinMarketCap → Fallback: CoinGecko
    """
    try:
        coin_data = await multi_source_service.get_coin_details(coin_id.lower())
        if not coin_data:
            raise HTTPException(status_code=404, detail="Cryptocurrency not found")
        return {"cryptocurrency": coin_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching {coin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch cryptocurrency details")


@router.get("/{coin_id}/history")
async def get_price_history(coin_id: str, days: int = 7):
    """
    Get price history for a cryptocurrency from multiple sources.
    Primary: CoinPaprika (up to 1 year) → Fallback: CoinGecko
    """
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        history = await multi_source_service.get_price_history(coin_id.lower(), days)
        return {"coin_id": coin_id, "days": days, "history": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching history for {coin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch price history")
