"""
CoinCap API Integration Service
Fetches real cryptocurrency prices from CoinCap API
Replaces CoinGecko for better rate limits (200 req/min free tier)

CoinCap API Documentation: https://docs.coincap.io/
"""
import httpx
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import random
from config import settings
from redis_cache import redis_cache

logger = logging.getLogger(__name__)


class CoinCapService:
    """
    Service for fetching cryptocurrency prices from CoinCap API.
    
    Features:
    - No authentication required (but API key available for higher limits)
    - 200 requests/minute on free tier (vs CoinGecko's ~10-30)
    - Real-time WebSocket support
    - Clean, consistent data format
    """
    
    def __init__(self):
        self.base_url = "https://api.coincap.io/v2"
        self.api_key = settings.coincap_api_key
        self.use_mock = settings.use_mock_prices
        self.timeout = 15  # seconds
        self._api_error_logged = False  # Track if API error was already logged
        
        # Top cryptocurrencies to track (CoinCap uses lowercase IDs)
        self.tracked_coins = [
            "bitcoin", "ethereum", "binance-coin", "cardano", "solana",
            "xrp", "polkadot", "dogecoin", "avalanche", "polygon",
            "chainlink", "litecoin", "uniswap", "stellar", "tron",
            "cosmos", "near-protocol", "bitcoin-cash", "algorand", "vechain"
        ]
        
        # Mapping from CoinCap IDs to common symbols
        self.id_to_symbol = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "binance-coin": "BNB",
            "cardano": "ADA",
            "solana": "SOL",
            "xrp": "XRP",
            "polkadot": "DOT",
            "dogecoin": "DOGE",
            "avalanche": "AVAX",
            "polygon": "MATIC",
            "chainlink": "LINK",
            "litecoin": "LTC",
            "uniswap": "UNI",
            "stellar": "XLM",
            "tron": "TRX",
            "cosmos": "ATOM",
            "near-protocol": "NEAR",
            "bitcoin-cash": "BCH",
            "algorand": "ALGO",
            "vechain": "VET",
        }
        
        # Reverse mapping
        self.symbol_to_id = {v: k for k, v in self.id_to_symbol.items()}
        
        logger.info(f"📊 CoinCap Service initialized (mock={self.use_mock})")
    
    async def get_prices(self, coin_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch current prices for top cryptocurrencies.
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
            prices = await self._fetch_real_prices(coin_ids)
            # Cache the results
            await redis_cache.cache_prices(prices)
            self._api_error_logged = False  # Reset on success
            return prices
        except Exception as e:
            # Only log API errors once to avoid log spam
            if not self._api_error_logged:
                logger.error(f"❌ CoinCap API error: {str(e)}. Falling back to mock data.")
                self._api_error_logged = True
            prices = self._get_mock_prices(coin_ids or self.tracked_coins)
            await redis_cache.cache_prices(prices)
            return prices
    
    async def _fetch_real_prices(self, coin_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch real prices from CoinCap API."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # CoinCap returns top assets sorted by rank, we'll fetch top 100
        url = f"{self.base_url}/assets"
        params = {
            "limit": 100  # Get top 100 cryptocurrencies
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        assets = data.get("data", [])
        logger.info(f"✅ Fetched {len(assets)} prices from CoinCap")
        
        # Transform to our format
        results = []
        for asset in assets:
            try:
                price = float(asset.get("priceUsd", 0))
                market_cap = float(asset.get("marketCapUsd", 0) or 0)
                volume_24h = float(asset.get("volumeUsd24Hr", 0) or 0)
                change_24h = float(asset.get("changePercent24Hr", 0) or 0)
                
                results.append({
                    "id": asset["id"],
                    "symbol": asset["symbol"].upper(),
                    "name": asset["name"],
                    "price": price,
                    "market_cap": market_cap,
                    "volume_24h": volume_24h,
                    "change_24h": round(change_24h, 2),
                    "rank": int(asset.get("rank", 0)),
                    "supply": float(asset.get("supply", 0) or 0),
                    "max_supply": float(asset.get("maxSupply", 0) or 0) if asset.get("maxSupply") else None,
                    "image": f"https://assets.coincap.io/assets/icons/{asset['symbol'].lower()}@2x.png",
                    "last_updated": datetime.utcnow().isoformat(),
                    "source": "coincap"
                })
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"⚠️ Error parsing asset {asset.get('id', 'unknown')}: {e}")
                continue
        
        return results
    
    async def get_specific_prices(self, coin_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch prices for specific coins by their IDs.
        """
        if self.use_mock:
            return self._get_mock_prices(coin_ids)
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        results = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for coin_id in coin_ids:
                try:
                    url = f"{self.base_url}/assets/{coin_id}"
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json().get("data", {})
                        price = float(data.get("priceUsd", 0))
                        market_cap = float(data.get("marketCapUsd", 0) or 0)
                        volume_24h = float(data.get("volumeUsd24Hr", 0) or 0)
                        change_24h = float(data.get("changePercent24Hr", 0) or 0)
                        
                        results.append({
                            "id": data["id"],
                            "symbol": data["symbol"].upper(),
                            "name": data["name"],
                            "price": price,
                            "market_cap": market_cap,
                            "volume_24h": volume_24h,
                            "change_24h": round(change_24h, 2),
                            "rank": int(data.get("rank", 0)),
                            "image": f"https://assets.coincap.io/assets/icons/{data['symbol'].lower()}@2x.png",
                            "last_updated": datetime.utcnow().isoformat(),
                            "source": "coincap"
                        })
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching {coin_id}: {e}")
                    continue
        
        return results
    
    def _get_mock_prices(self, coin_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate mock price data for development."""
        mock_data = {
            "bitcoin": {"name": "Bitcoin", "symbol": "BTC", "base_price": 68000, "rank": 1},
            "ethereum": {"name": "Ethereum", "symbol": "ETH", "base_price": 3500, "rank": 2},
            "binance-coin": {"name": "BNB", "symbol": "BNB", "base_price": 600, "rank": 3},
            "solana": {"name": "Solana", "symbol": "SOL", "base_price": 145, "rank": 4},
            "xrp": {"name": "XRP", "symbol": "XRP", "base_price": 0.58, "rank": 5},
            "cardano": {"name": "Cardano", "symbol": "ADA", "base_price": 0.65, "rank": 6},
            "dogecoin": {"name": "Dogecoin", "symbol": "DOGE", "base_price": 0.12, "rank": 7},
            "polkadot": {"name": "Polkadot", "symbol": "DOT", "base_price": 7.5, "rank": 8},
            "avalanche": {"name": "Avalanche", "symbol": "AVAX", "base_price": 35, "rank": 9},
            "polygon": {"name": "Polygon", "symbol": "MATIC", "base_price": 0.85, "rank": 10},
            "chainlink": {"name": "Chainlink", "symbol": "LINK", "base_price": 14.5, "rank": 11},
            "litecoin": {"name": "Litecoin", "symbol": "LTC", "base_price": 95, "rank": 12},
            "uniswap": {"name": "Uniswap", "symbol": "UNI", "base_price": 9.5, "rank": 13},
            "stellar": {"name": "Stellar", "symbol": "XLM", "base_price": 0.12, "rank": 14},
            "tron": {"name": "TRON", "symbol": "TRX", "base_price": 0.11, "rank": 15},
            "cosmos": {"name": "Cosmos", "symbol": "ATOM", "base_price": 9.0, "rank": 16},
            "near-protocol": {"name": "NEAR Protocol", "symbol": "NEAR", "base_price": 5.5, "rank": 17},
            "bitcoin-cash": {"name": "Bitcoin Cash", "symbol": "BCH", "base_price": 450, "rank": 18},
            "algorand": {"name": "Algorand", "symbol": "ALGO", "base_price": 0.22, "rank": 19},
            "vechain": {"name": "VeChain", "symbol": "VET", "base_price": 0.035, "rank": 20},
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
                    "rank": coin_info["rank"],
                    "image": f"https://assets.coincap.io/assets/icons/{coin_info['symbol'].lower()}@2x.png",
                    "last_updated": datetime.utcnow().isoformat(),
                    "source": "coincap_mock"
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
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            url = f"{self.base_url}/assets/{coin_id}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json().get("data", {})
            
            price = float(data.get("priceUsd", 0))
            market_cap = float(data.get("marketCapUsd", 0) or 0)
            volume_24h = float(data.get("volumeUsd24Hr", 0) or 0)
            change_24h = float(data.get("changePercent24Hr", 0) or 0)
            supply = float(data.get("supply", 0) or 0)
            max_supply = float(data.get("maxSupply", 0) or 0) if data.get("maxSupply") else None
            
            details = {
                "id": data["id"],
                "symbol": data["symbol"].upper(),
                "name": data["name"],
                "price": price,
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "change_24h": round(change_24h, 2),
                "rank": int(data.get("rank", 0)),
                "supply": supply,
                "max_supply": max_supply,
                "vwap_24h": float(data.get("vwap24Hr", 0) or 0),
                "explorer": data.get("explorer", ""),
                "image": f"https://assets.coincap.io/assets/icons/{data['symbol'].lower()}@2x.png",
                "last_updated": datetime.utcnow().isoformat(),
                "source": "coincap"
            }
            
            # Cache the details
            await redis_cache.cache_coin_details(coin_id, details)
            
            return details
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch details for {coin_id}: {str(e)}")
            return None
    
    async def get_price_history(self, coin_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get historical price data for charting.
        CoinCap provides free historical data with various intervals.
        """
        if self.use_mock:
            return self._get_mock_history(coin_id, days)
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Calculate time range
            end_time = int(datetime.utcnow().timestamp() * 1000)
            start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
            
            # Determine interval based on days
            if days <= 1:
                interval = "m5"  # 5 minutes
            elif days <= 7:
                interval = "h1"  # 1 hour
            elif days <= 30:
                interval = "h6"  # 6 hours
            else:
                interval = "d1"  # 1 day
            
            url = f"{self.base_url}/assets/{coin_id}/history"
            params = {
                "interval": interval,
                "start": start_time,
                "end": end_time
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            history_data = data.get("data", [])
            
            return [
                {
                    "timestamp": int(point["time"] / 1000),  # Convert to seconds
                    "price": float(point["priceUsd"]),
                    "date": point.get("date", "")
                }
                for point in history_data
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch history for {coin_id}: {str(e)}")
            return self._get_mock_history(coin_id, days)
    
    def _get_mock_history(self, coin_id: str, days: int) -> List[Dict[str, Any]]:
        """Generate mock historical data."""
        base_prices = {
            "bitcoin": 68000,
            "ethereum": 3500,
            "binance-coin": 600,
            "solana": 145,
        }
        base_price = base_prices.get(coin_id, 100)
        now = datetime.utcnow()
        
        history = []
        for i in range(days * 24):  # Hourly data
            timestamp = now - timedelta(hours=days * 24 - i)
            variation = random.uniform(-0.03, 0.03)
            price = base_price * (1 + variation)
            
            history.append({
                "timestamp": int(timestamp.timestamp()),
                "price": round(price, 2),
                "date": timestamp.isoformat()
            })
        
        return history
    
    async def get_markets(self, coin_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get market/exchange data for a specific coin.
        Shows where the coin is traded.
        """
        if self.use_mock:
            return []
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            url = f"{self.base_url}/assets/{coin_id}/markets"
            params = {"limit": limit}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            return [
                {
                    "exchange": market["exchangeId"],
                    "pair": f"{market['baseSymbol']}/{market['quoteSymbol']}",
                    "price": float(market.get("priceUsd", 0)),
                    "volume_24h": float(market.get("volumeUsd24Hr", 0) or 0),
                    "volume_percent": float(market.get("volumePercent", 0) or 0),
                }
                for market in data.get("data", [])
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch markets for {coin_id}: {str(e)}")
            return []
    
    async def search_assets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for assets by name or symbol.
        """
        if self.use_mock:
            return []
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            url = f"{self.base_url}/assets"
            params = {
                "search": query,
                "limit": limit
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            assets = data.get("data", [])
            
            return [
                {
                    "id": asset["id"],
                    "symbol": asset["symbol"].upper(),
                    "name": asset["name"],
                    "rank": int(asset.get("rank", 0)),
                    "price": float(asset.get("priceUsd", 0)),
                    "image": f"https://assets.coincap.io/assets/icons/{asset['symbol'].lower()}@2x.png",
                }
                for asset in assets
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to search assets: {str(e)}")
            return []


# Global service instance
coincap_service = CoinCapService()
