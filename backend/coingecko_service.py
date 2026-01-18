"""
CoinGecko API Integration Service
Fetches real cryptocurrency prices with fallback to mock data
Includes Redis caching for performance
"""
import httpx
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import random
from config import settings
from redis_cache import redis_cache

logger = logging.getLogger(__name__)


class CoinGeckoService:
    """Service for fetching cryptocurrency prices from CoinGecko API."""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.api_key = settings.coingecko_api_key
        self.use_mock = settings.use_mock_prices
        self.timeout = 10  # seconds
        
        # Popular cryptocurrencies to track
        self.tracked_coins = [
            "bitcoin", "ethereum", "binancecoin", "cardano", "solana",
            "ripple", "polkadot", "dogecoin", "avalanche-2", "polygon"
        ]
        
        logger.info(f"📊 CoinGecko Service initialized (mock={self.use_mock})")
    
    async def get_prices(self, coin_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch current prices for specified coins.
        Uses Redis cache for performance (60-second TTL).
        Falls back to mock data if USE_MOCK_PRICES=true or on API failure.
        """
        # Check cache first
        cached_prices = await redis_cache.get_cached_prices()
        if cached_prices:
            logger.info("✅ Using cached prices")
            return cached_prices
        
        if self.use_mock:
            logger.info("📊 Using mock price data")
            prices = self._get_mock_prices(coin_ids or self.tracked_coins)
            await redis_cache.cache_prices(prices)
            return prices
        
        try:
            prices = await self._fetch_real_prices(coin_ids or self.tracked_coins)
            # Cache the results
            await redis_cache.cache_prices(prices)
            return prices
        except Exception as e:
            logger.error(f"❌ CoinGecko API error: {str(e)}. Falling back to mock data.")
            prices = self._get_mock_prices(coin_ids or self.tracked_coins)
            await redis_cache.cache_prices(prices)
            return prices
    
    async def _fetch_real_prices(self, coin_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch real prices from CoinGecko API."""
        ids_param = ",".join(coin_ids)
        
        headers = {}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        
        url = f"{self.base_url}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids_param,
            "order": "market_cap_desc",
            "per_page": len(coin_ids),
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        logger.info(f"✅ Fetched {len(data)} prices from CoinGecko")
        
        # Transform to our format
        results = []
        for coin in data:
            results.append({
                "id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "price": coin["current_price"],
                "market_cap": coin["market_cap"],
                "volume_24h": coin["total_volume"],
                "change_24h": coin.get("price_change_percentage_24h", 0),
                "image": coin.get("image", ""),
                "last_updated": datetime.utcnow().isoformat()
            })
        
        return results
    
    def _get_mock_prices(self, coin_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate mock price data for development."""
        mock_data = {
            "bitcoin": {"name": "Bitcoin", "symbol": "BTC", "base_price": 45000},
            "ethereum": {"name": "Ethereum", "symbol": "ETH", "base_price": 2500},
            "binancecoin": {"name": "BNB", "symbol": "BNB", "base_price": 320},
            "cardano": {"name": "Cardano", "symbol": "ADA", "base_price": 0.52},
            "solana": {"name": "Solana", "symbol": "SOL", "base_price": 105},
            "ripple": {"name": "XRP", "symbol": "XRP", "base_price": 0.63},
            "polkadot": {"name": "Polkadot", "symbol": "DOT", "base_price": 7.2},
            "dogecoin": {"name": "Dogecoin", "symbol": "DOGE", "base_price": 0.083},
            "avalanche-2": {"name": "Avalanche", "symbol": "AVAX", "base_price": 38},
            "polygon": {"name": "Polygon", "symbol": "MATIC", "base_price": 0.92}
        }
        
        results = []
        for coin_id in coin_ids:
            if coin_id in mock_data:
                coin_info = mock_data[coin_id]
                base_price = coin_info["base_price"]
                
                # Add some random variation
                variation = random.uniform(-0.05, 0.05)  # ±5%
                current_price = base_price * (1 + variation)
                change_24h = random.uniform(-10, 10)
                
                results.append({
                    "id": coin_id,
                    "symbol": coin_info["symbol"],
                    "name": coin_info["name"],
                    "price": round(current_price, 8),
                    "market_cap": round(current_price * random.randint(10000000, 100000000), 2),
                    "volume_24h": round(current_price * random.randint(1000000, 10000000), 2),
                    "change_24h": round(change_24h, 2),
                    "image": f"https://assets.coingecko.com/coins/images/1/{coin_id}.png",
                    "last_updated": datetime.utcnow().isoformat()
                })
        
        return results
    
    async def get_coin_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific coin.
        Uses Redis cache (5-minute TTL).
        """
        # Check cache first
        cached_details = await redis_cache.get_cached_coin_details(coin_id)
        if cached_details:
            logger.info(f"✅ Using cached details for {coin_id}")
            return cached_details
        
        if self.use_mock:
            prices = self._get_mock_prices([coin_id])
            details = prices[0] if prices else None
            if details:
                await redis_cache.cache_coin_details(coin_id, details)
            return details
        
        try:
            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key
            
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                "localization": False,
                "tickers": False,
                "market_data": True,
                "community_data": False,
                "developer_data": False
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            market_data = data.get("market_data", {})
            
            details = {
                "id": data["id"],
                "symbol": data["symbol"].upper(),
                "name": data["name"],
                "price": market_data.get("current_price", {}).get("usd", 0),
                "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                "volume_24h": market_data.get("total_volume", {}).get("usd", 0),
                "change_24h": market_data.get("price_change_percentage_24h", 0),
                "ath": market_data.get("ath", {}).get("usd", 0),
                "ath_date": market_data.get("ath_date", {}).get("usd", ""),
                "atl": market_data.get("atl", {}).get("usd", 0),
                "circulating_supply": market_data.get("circulating_supply", 0),
                "total_supply": market_data.get("total_supply", 0),
                "image": data.get("image", {}).get("large", ""),
                "description": data.get("description", {}).get("en", "")[:500],  # Truncate
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Cache the details
            await redis_cache.cache_coin_details(coin_id, details)
            
            return details
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch details for {coin_id}: {str(e)}")
            return None
    
    async def get_price_history(self, coin_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get historical price data for charting."""
        if self.use_mock:
            return self._get_mock_history(coin_id, days)
        
        try:
            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key
            
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily" if days > 1 else "hourly"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            prices = data.get("prices", [])
            
            return [
                {
                    "timestamp": int(point[0] / 1000),  # Convert to seconds
                    "price": point[1]
                }
                for point in prices
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch history for {coin_id}: {str(e)}")
            return self._get_mock_history(coin_id, days)
    
    def _get_mock_history(self, coin_id: str, days: int) -> List[Dict[str, Any]]:
        """Generate mock historical data."""
        base_price = 45000 if coin_id == "bitcoin" else 2500
        now = datetime.utcnow()
        
        history = []
        for i in range(days * 24):  # Hourly data
            timestamp = now - timedelta(hours=days * 24 - i)
            variation = random.uniform(-0.03, 0.03)
            price = base_price * (1 + variation)
            
            history.append({
                "timestamp": int(timestamp.timestamp()),
                "price": round(price, 2)
            })
        
        return history


# Global service instance
coingecko_service = CoinGeckoService()
