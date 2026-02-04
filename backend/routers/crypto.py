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
    Primary: CoinCap (200 req/min) → Fallback: CoinPaprika
    """
    try:
        prices = await multi_source_service.get_prices()
        return {"cryptocurrencies": prices}
    except Exception as e:
        logger.error(f"❌ Error fetching cryptocurrencies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch cryptocurrency prices")


@router.get("/trading-pairs")
async def get_trading_pairs():
    """
    Get available trading pairs for the exchange.
    Returns common crypto pairs against USD.
    """
    # Return standard trading pairs based on available cryptocurrencies
    pairs = [
        "BTC/USD", "ETH/USD", "BNB/USD", "XRP/USD", "ADA/USD",
        "SOL/USD", "DOT/USD", "DOGE/USD", "MATIC/USD", "LTC/USD",
        "AVAX/USD", "LINK/USD", "UNI/USD", "ATOM/USD", "XLM/USD"
    ]
    return {"pairs": pairs}


@router.get("/{coin_id}")
async def get_cryptocurrency(coin_id: str):
    """
    Get specific cryptocurrency details from multiple sources.
    Primary: CoinCap → Fallback: CoinPaprika
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
    Primary: CoinCap (excellent historical data) → Fallback: CoinPaprika
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


