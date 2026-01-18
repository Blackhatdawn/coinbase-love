"""
WebSocket Price Feed Service
Real-time cryptocurrency price updates via WebSocket
Uses CoinGecko API with proper rate limiting and caching
"""
import os
import json
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class PriceFeedManager:
    """Manages WebSocket connections and price broadcasting"""
    
    def __init__(self):
        self.connections: Set = set()
        self.prices: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.last_api_call: Optional[datetime] = None
        
        # RATE LIMITING - CoinGecko free tier allows ~10-30 calls/min
        # With API key, we can be more aggressive
        coingecko_api_key = os.environ.get('COINGECKO_API_KEY')
        self.api_key = coingecko_api_key
        self.update_interval = 15 if coingecko_api_key else 30  # Faster with API key
        self.min_api_interval = 5 if coingecko_api_key else 10  # Minimum interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.backoff_multiplier = 1
        
        # Top coins to track
        self.tracked_coins = [
            "bitcoin", "ethereum", "binancecoin", "solana", 
            "ripple", "cardano", "dogecoin", "avalanche-2",
            "polkadot", "chainlink", "polygon", "litecoin"
        ]
    
    async def start(self):
        """Start the price feed background task"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._price_update_loop())
        logger.info("📡 Price feed started (interval: %ds)", self.update_interval)
    
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
        """Fetch prices from CoinGecko API with rate limiting"""
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
                headers["x-cg-pro-api-key"] = self.api_key
            
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": ",".join(self.tracked_coins),
                        "vs_currencies": "usd",
                        "include_24hr_change": "true",
                        "include_market_cap": "true",
                        "include_24hr_vol": "true"
                    },
                    headers=headers
                )
                
                self.last_api_call = datetime.now()
                
                if response.status_code == 200:
                    self.consecutive_errors = 0
                    self.backoff_multiplier = 1
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - increase backoff
                    self.consecutive_errors += 1
                    self.backoff_multiplier = min(self.backoff_multiplier * 2, 8)
                    logger.warning(f"⚠️ CoinGecko rate limited (429). Backoff: {self.backoff_multiplier}x")
                    return {}
                else:
                    logger.warning(f"CoinGecko API returned {response.status_code}")
                    return {}
                    
        except httpx.TimeoutException:
            logger.warning("⏱️ CoinGecko API timeout")
            self.consecutive_errors += 1
            return {}
        except Exception as e:
            logger.error(f"Price fetch error: {e}")
            self.consecutive_errors += 1
            return {}
    
    async def _price_update_loop(self):
        """Background loop to fetch and broadcast prices"""
        while self.is_running:
            try:
                # Check if we have too many errors
                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.error(f"❌ Too many consecutive errors ({self.consecutive_errors}). Pausing for 5 minutes.")
                    await asyncio.sleep(300)  # 5 minute pause
                    self.consecutive_errors = 0
                    self.backoff_multiplier = 1
                    continue
                
                # Fetch new prices
                raw_prices = await self._fetch_prices()
                
                if raw_prices:
                    # Transform to our format
                    formatted_prices = self._format_prices(raw_prices)
                    
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
                            "changes": changes,
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
    
    def _format_prices(self, raw: Dict) -> Dict[str, Any]:
        """Format raw CoinGecko data to our structure"""
        symbol_map = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "binancecoin": "BNB",
            "solana": "SOL",
            "ripple": "XRP",
            "cardano": "ADA",
            "dogecoin": "DOGE",
            "avalanche-2": "AVAX",
            "polkadot": "DOT",
            "chainlink": "LINK",
            "polygon": "MATIC",
            "litecoin": "LTC"
        }
        
        formatted = {}
        for coin_id, data in raw.items():
            symbol = symbol_map.get(coin_id, coin_id.upper())
            formatted[symbol] = {
                "symbol": symbol,
                "id": coin_id,
                "price": data.get("usd", 0),
                "change_24h": data.get("usd_24h_change", 0),
                "market_cap": data.get("usd_market_cap", 0),
                "volume_24h": data.get("usd_24h_vol", 0)
            }
        
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
            "last_update": self.last_update.isoformat() if self.last_update else None
        }


# Global price feed manager
price_feed = PriceFeedManager()
