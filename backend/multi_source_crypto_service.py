"""
Multi-Source Cryptocurrency Data Service
Primary sources: CoinPaprika, CoinMarketCap
Fallback source: CoinGecko
Provides redundant data fetching with automatic fallback
"""
import httpx
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from config import settings
from redis_cache import redis_cache
from coingecko_service import coingecko_service

logger = logging.getLogger(__name__)


class MultiSourceCryptoService:
    """
    Fetches cryptocurrency data from multiple sources with automatic fallback.
    Priority order: CoinPaprika → CoinMarketCap → CoinGecko
    """
    
    def __init__(self):
        # API Configuration
        self.coinpaprika_base = "https://api.coinpaprika.com/v1"
        self.coinmarketcap_base = "https://pro-api.coinmarketcap.com/v1"
        self.coinmarketcap_key = settings.coinmarketcap_api_key
        
        # Timeout for API calls
        self.timeout = 10  # seconds
        
        # Coin ID mappings (CoinPaprika uses different IDs)
        self.coin_id_map = {
            "bitcoin": {"paprika": "btc-bitcoin", "cmc": "BTC"},
            "ethereum": {"paprika": "eth-ethereum", "cmc": "ETH"},
            "binancecoin": {"paprika": "bnb-binance-coin", "cmc": "BNB"},
            "cardano": {"paprika": "ada-cardano", "cmc": "ADA"},
            "solana": {"paprika": "sol-solana", "cmc": "SOL"},
            "ripple": {"paprika": "xrp-xrp", "cmc": "XRP"},
            "polkadot": {"paprika": "dot-polkadot", "cmc": "DOT"},
            "dogecoin": {"paprika": "doge-dogecoin", "cmc": "DOGE"},
            "avalanche-2": {"paprika": "avax-avalanche", "cmc": "AVAX"},
            "polygon": {"paprika": "matic-polygon", "cmc": "MATIC"},
        }
        
        # Popular cryptocurrencies to track
        self.tracked_coins = list(self.coin_id_map.keys())
        
        logger.info("🌐 Multi-Source Crypto Service initialized")
        logger.info("📊 Sources: CoinPaprika (primary) → CoinMarketCap (secondary) → CoinGecko (fallback)")
    
    async def get_prices(self, coin_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch current prices for specified coins with multi-source fallback.
        Tries CoinPaprika first, then CoinMarketCap, finally CoinGecko.
        """
        coins_to_fetch = coin_ids or self.tracked_coins
        
        # Check cache first
        cached_prices = await redis_cache.get_cached_prices()
        if cached_prices:
            logger.info("✅ Using cached prices")
            return cached_prices
        
        # Try CoinPaprika first (PRIMARY)
        try:
            logger.info("📊 Attempting to fetch from CoinPaprika (primary)...")
            prices = await self._fetch_from_coinpaprika(coins_to_fetch)
            if prices:
                logger.info(f"✅ Successfully fetched {len(prices)} prices from CoinPaprika")
                await redis_cache.cache_prices(prices)
                return prices
        except Exception as e:
            logger.warning(f"⚠️ CoinPaprika failed: {str(e)}")
        
        # Try CoinMarketCap (SECONDARY)
        try:
            logger.info("📊 Attempting to fetch from CoinMarketCap (secondary)...")
            prices = await self._fetch_from_coinmarketcap(coins_to_fetch)
            if prices:
                logger.info(f"✅ Successfully fetched {len(prices)} prices from CoinMarketCap")
                await redis_cache.cache_prices(prices)
                return prices
        except Exception as e:
            logger.warning(f"⚠️ CoinMarketCap failed: {str(e)}")
        
        # Fallback to CoinGecko (FALLBACK)
        try:
            logger.info("📊 Falling back to CoinGecko...")
            prices = await coingecko_service.get_prices(coins_to_fetch)
            logger.info(f"✅ Successfully fetched {len(prices)} prices from CoinGecko (fallback)")
            await redis_cache.cache_prices(prices)
            return prices
        except Exception as e:
            logger.error(f"❌ All sources failed. Using mock data. Error: {str(e)}")
            # Return mock data as last resort
            return coingecko_service._get_mock_prices(coins_to_fetch)
    
    async def _fetch_from_coinpaprika(self, coin_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch prices from CoinPaprika API (no authentication required)."""
        prices = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for coin_id in coin_ids:
                try:
                    # Get CoinPaprika ID
                    paprika_id = self.coin_id_map.get(coin_id, {}).get("paprika")
                    if not paprika_id:
                        logger.warning(f"⚠️ No CoinPaprika ID mapping for {coin_id}")
                        continue
                    
                    # Fetch ticker data
                    url = f"{self.coinpaprika_base}/tickers/{paprika_id}"
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract price data
                    quote = data.get("quotes", {}).get("USD", {})
                    prices.append({
                        "id": coin_id,
                        "symbol": data.get("symbol", "").upper(),
                        "name": data.get("name", ""),
                        "price": quote.get("price", 0),
                        "market_cap": quote.get("market_cap", 0),
                        "volume_24h": quote.get("volume_24h", 0),
                        "change_24h": quote.get("percent_change_24h", 0),
                        "image": "",  # CoinPaprika doesn't provide images
                        "last_updated": data.get("last_updated", datetime.now().isoformat()),
                        "source": "coinpaprika"
                    })
                except Exception as e:
                    logger.warning(f"⚠️ CoinPaprika error for {coin_id}: {str(e)}")
                    continue
        
        return prices
    
    async def _fetch_from_coinmarketcap(self, coin_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch prices from CoinMarketCap API (requires API key)."""
        if not self.coinmarketcap_key:
            logger.warning("⚠️ CoinMarketCap API key not configured")
            raise Exception("CoinMarketCap API key not configured")
        
        # Convert coin IDs to CMC symbols
        symbols = []
        for coin_id in coin_ids:
            cmc_symbol = self.coin_id_map.get(coin_id, {}).get("cmc")
            if cmc_symbol:
                symbols.append(cmc_symbol)
        
        if not symbols:
            raise Exception("No valid symbols for CoinMarketCap")
        
        prices = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.coinmarketcap_base}/cryptocurrency/quotes/latest"
                headers = {
                    "Accepts": "application/json",
                    "X-CMC_PRO_API_KEY": self.coinmarketcap_key
                }
                params = {
                    "symbol": ",".join(symbols),
                    "convert": "USD"
                }
                
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Parse response
                for coin_id in coin_ids:
                    cmc_symbol = self.coin_id_map.get(coin_id, {}).get("cmc")
                    if not cmc_symbol or cmc_symbol not in data.get("data", {}):
                        continue
                    
                    coin_data = data["data"][cmc_symbol][0]
                    quote = coin_data.get("quote", {}).get("USD", {})
                    
                    prices.append({
                        "id": coin_id,
                        "symbol": coin_data.get("symbol", ""),
                        "name": coin_data.get("name", ""),
                        "price": quote.get("price", 0),
                        "market_cap": quote.get("market_cap", 0),
                        "volume_24h": quote.get("volume_24h", 0),
                        "change_24h": quote.get("percent_change_24h", 0),
                        "image": "",  # CMC doesn't provide images in this endpoint
                        "last_updated": quote.get("last_updated", datetime.now().isoformat()),
                        "source": "coinmarketcap"
                    })
            except Exception as e:
                logger.warning(f"⚠️ CoinMarketCap error: {str(e)}")
                raise
        
        return prices
    
    async def get_coin_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific cryptocurrency.
        Tries multiple sources with fallback.
        """
        # Try CoinPaprika first
        try:
            paprika_id = self.coin_id_map.get(coin_id, {}).get("paprika")
            if paprika_id:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    url = f"{self.coinpaprika_base}/tickers/{paprika_id}"
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    quote = data.get("quotes", {}).get("USD", {})
                    return {
                        "id": coin_id,
                        "symbol": data.get("symbol", "").upper(),
                        "name": data.get("name", ""),
                        "price": quote.get("price", 0),
                        "market_cap": quote.get("market_cap", 0),
                        "volume_24h": quote.get("volume_24h", 0),
                        "change_24h": quote.get("percent_change_24h", 0),
                        "circulating_supply": data.get("circulating_supply", 0),
                        "total_supply": data.get("total_supply", 0),
                        "max_supply": data.get("max_supply", 0),
                        "rank": data.get("rank", 0),
                        "source": "coinpaprika"
                    }
        except Exception as e:
            logger.warning(f"⚠️ CoinPaprika details failed: {str(e)}")
        
        # Fallback to CoinGecko
        return await coingecko_service.get_coin_details(coin_id)
    
    async def get_price_history(self, coin_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get historical price data.
        CoinPaprika supports up to 1 year for free tier.
        Falls back to CoinGecko if needed.
        """
        # Try CoinPaprika first
        try:
            paprika_id = self.coin_id_map.get(coin_id, {}).get("paprika")
            if paprika_id and days <= 365:  # Free tier limit
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Calculate start date
                    from datetime import timedelta
                    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    url = f"{self.coinpaprika_base}/coins/{paprika_id}/ohlcv/historical"
                    params = {
                        "start": start_date,
                        "interval": "1d" if days > 1 else "1h"
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Convert to our format
                    history = []
                    for point in data:
                        timestamp = int(datetime.fromisoformat(point["time_close"].replace("Z", "+00:00")).timestamp())
                        history.append({
                            "timestamp": timestamp,
                            "price": point.get("close", 0)
                        })
                    
                    return history
        except Exception as e:
            logger.warning(f"⚠️ CoinPaprika history failed: {str(e)}")
        
        # Fallback to CoinGecko
        return await coingecko_service.get_price_history(coin_id, days)


# Global instance
multi_source_service = MultiSourceCryptoService()
