"""
Multi-Source Cryptocurrency Data Service
Primary source: CoinGecko (reliable public market API)
Secondary source: CoinPaprika (free, no auth needed)
Provides redundant data fetching with automatic fallback

"""
import httpx
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from config import settings
from redis_cache import redis_cache
from coincap_service import coincap_service

logger = logging.getLogger(__name__)


class MultiSourceCryptoService:
    """
    Fetches cryptocurrency data from multiple sources with automatic fallback.
    Priority order: CoinGecko (primary) → CoinPaprika (fallback)
    
    Why this order:
    - CoinGecko: mature market API, broad asset coverage
    - CoinPaprika: No auth required, good fallback
    """
    
    def __init__(self):
        # API Configuration
        self.coinpaprika_base = "https://api.coinpaprika.com/v1"
        
        # Timeout for API calls
        self.timeout = 15  # seconds
        
        # Coin ID mappings (CoinPaprika uses different IDs)
        self.coin_id_map = {
            "bitcoin": {"paprika": "btc-bitcoin", "symbol": "BTC"},
            "ethereum": {"paprika": "eth-ethereum", "symbol": "ETH"},
            "binance-coin": {"paprika": "bnb-binance-coin", "symbol": "BNB"},
            "cardano": {"paprika": "ada-cardano", "symbol": "ADA"},
            "solana": {"paprika": "sol-solana", "symbol": "SOL"},
            "xrp": {"paprika": "xrp-xrp", "symbol": "XRP"},
            "polkadot": {"paprika": "dot-polkadot", "symbol": "DOT"},
            "dogecoin": {"paprika": "doge-dogecoin", "symbol": "DOGE"},
            "avalanche": {"paprika": "avax-avalanche", "symbol": "AVAX"},
            "polygon": {"paprika": "matic-polygon", "symbol": "MATIC"},
            "chainlink": {"paprika": "link-chainlink", "symbol": "LINK"},
            "litecoin": {"paprika": "ltc-litecoin", "symbol": "LTC"},
            "uniswap": {"paprika": "uni-uniswap", "symbol": "UNI"},
            "stellar": {"paprika": "xlm-stellar", "symbol": "XLM"},
            "tron": {"paprika": "trx-tron", "symbol": "TRX"},
            "cosmos": {"paprika": "atom-cosmos", "symbol": "ATOM"},
            "near-protocol": {"paprika": "near-near-protocol", "symbol": "NEAR"},
            "bitcoin-cash": {"paprika": "bch-bitcoin-cash", "symbol": "BCH"},
            "algorand": {"paprika": "algo-algorand", "symbol": "ALGO"},
            "vechain": {"paprika": "vet-vechain", "symbol": "VET"},
        }
        
        # Popular cryptocurrencies to track
        self.tracked_coins = list(self.coin_id_map.keys())
        
        logger.info("🌐 Multi-Source Crypto Service initialized")
        logger.info("📊 Sources: CoinGecko (primary) → CoinPaprika (fallback)")
    
    async def get_prices(self, coin_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch current prices for specified coins with multi-source fallback.
        Tries CoinGecko first, then CoinPaprika as fallback.
        """
        coins_to_fetch = coin_ids or self.tracked_coins
        
        # Check cache first
        cached_prices = await redis_cache.get_cached_prices()
        if cached_prices:
            logger.info("✅ Using cached prices")
            return cached_prices
        
        # Try CoinGecko first (PRIMARY)
        try:
            logger.info("📊 Fetching from CoinGecko (primary)...")
            prices = await coincap_service.get_prices(coins_to_fetch)
            if prices:
                logger.info(f"✅ Successfully fetched {len(prices)} prices from CoinGecko")
                await redis_cache.cache_prices(prices)
                return prices
        except Exception as e:
            logger.warning(f"⚠️ CoinGecko failed: {str(e)}")
        
        # Try CoinPaprika (FALLBACK)
        try:
            logger.info("📊 Falling back to CoinPaprika...")
            prices = await self._fetch_from_coinpaprika(coins_to_fetch)
            if prices:
                logger.info(f"✅ Successfully fetched {len(prices)} prices from CoinPaprika")
                await redis_cache.cache_prices(prices)
                return prices
        except Exception as e:
            logger.warning(f"⚠️ CoinPaprika failed: {str(e)}")
        
        # Return mock data as last resort
        logger.error("❌ All sources failed. Using mock data.")
        return coincap_service._get_mock_prices(coins_to_fetch)
    
    async def _fetch_from_coinpaprika(self, coin_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch prices from CoinPaprika API (no authentication required)."""
        prices = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for coin_id in coin_ids:
                try:
                    # Get CoinPaprika ID
                    paprika_id = self.coin_id_map.get(coin_id, {}).get("paprika")
                    if not paprika_id:
                        # Try direct ID as fallback
                        paprika_id = coin_id
                    
                    # Fetch ticker data
                    url = f"{self.coinpaprika_base}/tickers/{paprika_id}"
                    response = await client.get(url)
                    
                    if response.status_code != 200:
                        continue
                    
                    data = response.json()
                    
                    # Extract price data
                    quote = data.get("quotes", {}).get("USD", {})
                    symbol = data.get("symbol", "").upper()
                    
                    prices.append({
                        "id": coin_id,
                        "symbol": symbol,
                        "name": data.get("name", ""),
                        "price": quote.get("price", 0),
                        "market_cap": quote.get("market_cap", 0),
                        "volume_24h": quote.get("volume_24h", 0),
                        "change_24h": quote.get("percent_change_24h", 0),
                        "rank": data.get("rank", 0),
                        "image": "",
                        "last_updated": data.get("last_updated", datetime.now().isoformat()),
                        "source": "coinpaprika"
                    })
                except Exception as e:
                    logger.warning(f"⚠️ CoinPaprika error for {coin_id}: {str(e)}")
                    continue
        
        return prices
    
    async def get_coin_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific cryptocurrency.
        Tries CoinGecko first, then CoinPaprika as fallback.
        """
        # Try CoinGecko first
        try:
            details = await coincap_service.get_coin_details(coin_id)
            if details:
                return details
        except Exception as e:
            logger.warning(f"⚠️ CoinGecko details failed: {str(e)}")
        
        # Fallback to CoinPaprika
        try:
            paprika_id = self.coin_id_map.get(coin_id, {}).get("paprika", coin_id)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.coinpaprika_base}/tickers/{paprika_id}"
                response = await client.get(url)
                
                if response.status_code == 200:
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
        
        return None
    
    async def get_price_history(self, coin_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get historical price data.
        CoinGecko provides robust historical data.
        Falls back to CoinPaprika if needed.
        """
        # Try CoinGecko first (better historical data)
        try:
            history = await coincap_service.get_price_history(coin_id, days)
            if history:
                return history
        except Exception as e:
            logger.warning(f"⚠️ CoinGecko history failed: {str(e)}")
        
        # Fallback to CoinPaprika
        try:
            paprika_id = self.coin_id_map.get(coin_id, {}).get("paprika", coin_id)
            
            if days <= 365:  # Free tier limit
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    from datetime import timedelta
                    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    url = f"{self.coinpaprika_base}/coins/{paprika_id}/ohlcv/historical"
                    params = {
                        "start": start_date,
                        "interval": "1d" if days > 1 else "1h"
                    }
                    
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        history = []
                        for point in data:
                            timestamp = int(datetime.fromisoformat(
                                point["time_close"].replace("Z", "+00:00")
                            ).timestamp())
                            history.append({
                                "timestamp": timestamp,
                                "price": point.get("close", 0)
                            })
                        return history
        except Exception as e:
            logger.warning(f"⚠️ CoinPaprika history failed: {str(e)}")
        
        # Return mock history as last resort
        return coincap_service._get_mock_history(coin_id, days)
    
    async def search_assets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for cryptocurrency assets by name or symbol."""
        try:
            return await coincap_service.search_assets(query, limit)
        except Exception as e:
            logger.warning(f"⚠️ Search failed: {str(e)}")
            return []
    
    async def get_markets(self, coin_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get market/exchange data for a specific coin."""
        try:
            return await coincap_service.get_markets(coin_id, limit)
        except Exception as e:
            logger.warning(f"⚠️ Markets fetch failed: {str(e)}")
            return []


# Global instance
multi_source_service = MultiSourceCryptoService()
