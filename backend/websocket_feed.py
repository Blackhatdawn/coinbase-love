"""
WebSocket Price Feed Service
Real-time cryptocurrency price updates via WebSocket
Uses CoinCap API with excellent rate limiting (200 req/min free tier)
"""
import json
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
import httpx

from config import settings

logger = logging.getLogger(__name__)


class PriceFeedManager:
    """
    Manages WebSocket connections and price broadcasting.
    Uses CoinCap API for reliable, rate-limit-friendly price data.
    """
    
    def __init__(self):
        self.connections: Set = set()
        self.prices: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.last_api_call: Optional[datetime] = None
        
        # CoinCap has generous rate limits (200 req/min free tier)
        # With API key, even higher limits available
        self.api_key = settings.coincap_api_key
        self.update_interval = 10 if self.api_key else 15  # Faster updates with API key
        self.min_api_interval = 3 if self.api_key else 5  # Minimum interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.backoff_multiplier = 1
        
        # Top coins to track (using CoinCap IDs)
        self.tracked_coins = [
            "bitcoin", "ethereum", "binance-coin", "solana", 
            "xrp", "cardano", "dogecoin", "avalanche",
            "polkadot", "chainlink", "polygon", "litecoin",
            "uniswap", "stellar", "tron", "cosmos"
        ]
        
        # Symbol mapping
        self.symbol_map = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "binance-coin": "BNB",
            "solana": "SOL",
            "xrp": "XRP",
            "cardano": "ADA",
            "dogecoin": "DOGE",
            "avalanche": "AVAX",
            "polkadot": "DOT",
            "chainlink": "LINK",
            "polygon": "MATIC",
            "litecoin": "LTC",
            "uniswap": "UNI",
            "stellar": "XLM",
            "tron": "TRX",
            "cosmos": "ATOM",
            "near-protocol": "NEAR",
            "bitcoin-cash": "BCH",
        }
    
    async def start(self):
        """Start the price feed background task"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._price_update_loop())
        logger.info("📡 Price feed started (CoinCap API, interval: %ds)", self.update_interval)
    
    async def stop(self):
        """Stop the price feed"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("📡 Price feed stopped")
    
    def add_connection(self, websocket):
        """Add a WebSocket connection"""
        self.connections.add(websocket)
        logger.info(f"📡 WebSocket connected (total: {len(self.connections)})")
    
    def remove_connection(self, websocket):
        """Remove a WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"📡 WebSocket disconnected (total: {len(self.connections)})")
    
    async def _fetch_prices(self) -> Dict[str, Any]:
        """Fetch prices from CoinCap API with rate limiting and fallback"""
        # Enforce minimum interval between API calls
        if self.last_api_call:
            time_since_last = (datetime.now() - self.last_api_call).total_seconds()
            if time_since_last < self.min_api_interval:
                wait_time = self.min_api_interval - time_since_last
                logger.debug(f"⏳ Rate limiting: waiting {wait_time:.1f}s before API call")
                await asyncio.sleep(wait_time)
        
        try:
            # Use API key if available for higher rate limits
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                logger.debug(f"🔑 Using CoinCap API key: {self.api_key[:8]}...")
            
            # Get URL from config or use default
            coincap_api_url = getattr(settings, 'coincap_api_url', 'https://api.coincap.io/v2')
            
            async with httpx.AsyncClient(timeout=15) as client:
                # CoinCap /assets endpoint returns all top cryptocurrencies
                response = await client.get(
                    f"{coincap_api_url}/assets",
                    params={"limit": 50},  # Get top 50 coins
                    headers=headers
                )
                
                self.last_api_call = datetime.now()
                
                if response.status_code == 200:
                    self.consecutive_errors = 0
                    self.backoff_multiplier = 1
                    data = response.json()
                    logger.info(f"✅ Fetched {len(data.get('data', []))} prices from CoinCap API")
                    return data
                elif response.status_code == 429:
                    # Rate limited - increase backoff
                    self.consecutive_errors += 1
                    self.backoff_multiplier = min(self.backoff_multiplier * 2, 8)
                    logger.warning(
                        f"⚠️ CoinCap rate limited (429). Backoff: {self.backoff_multiplier}x. "
                        f"ACTION: Consider upgrading API plan or reducing request frequency"
                    )
                    return {}
                elif response.status_code == 401:
                    logger.error(
                        "❌ CoinCap API authentication failed (401). "
                        "ACTION: Verify COINCAP_API_KEY is correct in environment variables"
                    )
                    return {}
                else:
                    logger.warning(f"CoinCap API returned {response.status_code}: {response.text[:200]}")
                    return {}
                    
        except httpx.TimeoutException:
            logger.warning(
                "⏱️ CoinCap API timeout. "
                "ACTION: Check network latency or increase timeout value"
            )
            self.consecutive_errors += 1
            return {}
        except httpx.ConnectError as e:
            error_str = str(e)
            # DNS or connection errors - try fallback
            if "Name or service not known" in error_str or "getaddrinfo failed" in error_str:
                logger.warning(
                    "🌐 DNS resolution failed for CoinCap API. "
                    "ACTION: Check network connectivity and DNS settings. "
                    "If on Render, ensure outbound network access is enabled. "
                    "Falling back to cached/mock data."
                )
            elif "Connection refused" in error_str:
                logger.warning(
                    "🔌 Connection refused by CoinCap API. "
                    "ACTION: CoinCap may be blocking this IP or experiencing issues"
                )
            else:
                logger.warning(f"🔌 Connection error: {e}")
            self.consecutive_errors += 1
            return {}
        except Exception as e:
            logger.error(
                f"❌ Price fetch error: {e}. "
                f"ACTION: Review exception and check CoinCap API status"
            )
            self.consecutive_errors += 1
            return {}
    
    async def _price_update_loop(self):
        """Background loop to fetch and broadcast prices"""
        while self.is_running:
            try:
                # Check if we have too many errors
                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.error(f"❌ Too many consecutive errors ({self.consecutive_errors}). Pausing for 2 minutes.")
                    await asyncio.sleep(120)  # 2 minute pause (shorter than before)
                    self.consecutive_errors = 0
                    self.backoff_multiplier = 1
                    continue
                
                # Fetch new prices
                raw_data = await self._fetch_prices()
                
                if raw_data and raw_data.get("data"):
                    # Transform to our format
                    formatted_prices = self._format_prices(raw_data["data"])
                    
                    # Detect changes
                    changes = self._detect_changes(formatted_prices)
                    
                    # Update stored prices
                    self.prices = formatted_prices
                    self.last_update = datetime.utcnow()
                    
                    # Broadcast to all connections (only if there are connections)
                    if self.connections:
                        await self._broadcast({
                            "type": "price_update",
                            "data": formatted_prices,
                            "prices": {k: str(v["price"]) for k, v in formatted_prices.items()},
                            "changes": changes,
                            "source": "coincap",
                            "timestamp": self.last_update.isoformat()
                        })
                
                # Calculate next interval with backoff
                actual_interval = self.update_interval * self.backoff_multiplier
                logger.debug(f"⏳ Next update in {actual_interval}s")
                await asyncio.sleep(actual_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Price update loop error: {e}")
                await asyncio.sleep(10)
    
    def _format_prices(self, assets: list) -> Dict[str, Any]:
        """Format raw CoinCap data to our structure"""
        formatted = {}
        
        for asset in assets:
            try:
                coin_id = asset.get("id", "")
                symbol = asset.get("symbol", "").upper()
                
                # Use symbol as the key for easier frontend access
                formatted[symbol.lower()] = {
                    "symbol": symbol,
                    "id": coin_id,
                    "name": asset.get("name", ""),
                    "price": float(asset.get("priceUsd", 0)),
                    "change_24h": float(asset.get("changePercent24Hr", 0) or 0),
                    "market_cap": float(asset.get("marketCapUsd", 0) or 0),
                    "volume_24h": float(asset.get("volumeUsd24Hr", 0) or 0),
                    "rank": int(asset.get("rank", 0)),
                }
            except (ValueError, TypeError):
                continue
        
        return formatted
    
    def _detect_changes(self, new_prices: Dict) -> Dict[str, str]:
        """Detect price direction changes"""
        changes = {}
        
        for symbol, data in new_prices.items():
            old_price = self.prices.get(symbol, {}).get("price", 0)
            new_price = data["price"]
            
            if old_price > 0:
                if new_price > old_price:
                    changes[symbol] = "up"
                elif new_price < old_price:
                    changes[symbol] = "down"
                else:
                    changes[symbol] = "unchanged"
        
        return changes
    
    async def _broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
        
        data = json.dumps(message)
        disconnected = set()
        
        for ws in self.connections:
            try:
                await ws.send_text(data)
            except Exception as e:
                logger.debug(f"WebSocket send error: {e}")
                disconnected.add(ws)
        
        # Clean up disconnected
        for ws in disconnected:
            self.connections.discard(ws)
    
    async def send_to_client(self, websocket, message: Dict):
        """Send message to specific client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Send to client error: {e}")
    
    def get_current_prices(self) -> Dict[str, Any]:
        """Get current cached prices"""
        return {
            "prices": self.prices,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "source": "coincap"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "is_running": self.is_running,
            "connected_clients": len(self.connections),
            "prices_cached": len(self.prices),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "consecutive_errors": self.consecutive_errors,
            "backoff_multiplier": self.backoff_multiplier,
            "source": "coincap"
        }


# Global price feed manager
price_feed = PriceFeedManager()
