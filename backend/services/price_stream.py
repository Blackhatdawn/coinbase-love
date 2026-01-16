"""
PriceStreamService
Real-time cryptocurrency price streaming service.
Connects to CoinCap WebSocket, parses prices, and updates Redis cache.

Architecture:
1. Connect to CoinCap WebSocket (primary source)
2. Parse JSON stream and update Redis with 30s TTL
3. Auto-reconnect on disconnect with exponential backoff
4. Fallback to Binance if CoinCap unavailable >30s
5. Monitor connection health with detailed logging
"""

import asyncio
import json
import logging
import time
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import websockets
import httpx

from redis_cache import redis_cache

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    SWITCHING_SOURCE = "switching_source"
    OFFLINE = "offline"


class PriceStreamService:
    """
    Real-time price streaming service with automatic failover.
    Connects to CoinCap primary, falls back to Binance if needed.
    """
    
    def __init__(self):
        # Connection management
        self.state = ConnectionState.DISCONNECTED
        self.is_running = False
        self.websocket = None
        self.current_source = "coincap"  # or "binance"
        
        # Reconnection strategy
        self.reconnect_attempt = 0
        self.max_reconnect_attempts = 10
        self.base_backoff = 1  # seconds
        self.max_backoff = 30  # seconds
        self.last_reconnect_time = 0
        
        # WebSocket endpoints
        self.COINCAP_WS = "wss://ws.coincap.io/prices?assets=ALL"
        self.BINANCE_WS = "wss://stream.binance.com:9443/ws/!ticker@arr"
        
        # Price tracking
        self.prices: Dict[str, float] = {}
        self.last_update = datetime.now()
        self.symbol_mapping = self._build_symbol_mapping()
        
        # Fallback timeout: switch to Binance if CoinCap down >30s
        self.fallback_timeout = 30
        self.last_successful_update = datetime.now()
        
        # Tasks
        self._task: Optional[asyncio.Task] = None
        self._fallback_task: Optional[asyncio.Task] = None
        
        logger.info("🚀 PriceStreamService initialized (source: CoinCap primary)")
    
    def _build_symbol_mapping(self) -> Dict[str, str]:
        """Map coin symbols to their canonical IDs"""
        return {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "LINK": "chainlink",
            "MATIC": "polygon",
            "LTC": "litecoin",
            "UNI": "uniswap",
            "ATOM": "cosmos",
            "XLM": "stellar",
            "NEAR": "near",
            "ARB": "arbitrum",
            "OP": "optimism",
        }
    
    # ============================================
    # LIFECYCLE METHODS
    # ============================================
    
    async def start(self) -> None:
        """Start the price stream service"""
        if self.is_running:
            logger.warning("⚠️ PriceStreamService already running")
            return
        
        self.is_running = True
        self.reconnect_attempt = 0
        
        logger.info("✅ Starting PriceStreamService")
        self._task = asyncio.create_task(self._stream_loop())
        
        # Start fallback monitor
        self._fallback_task = asyncio.create_task(self._fallback_monitor())
    
    async def stop(self) -> None:
        """Stop the price stream service"""
        self.is_running = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"⚠️ Error closing WebSocket: {e}")
        
        if self._task:
            self._task.cancel()
        
        if self._fallback_task:
            self._fallback_task.cancel()
        
        self._update_state(ConnectionState.DISCONNECTED)
        logger.info("🛑 PriceStreamService stopped")
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        # Try cache first
        cache_key = f"crypto:price:{symbol.lower()}"
        cached = await redis_cache.get(cache_key)
        if cached:
            return float(cached)
        
        # Return in-memory if available
        if symbol in self.prices:
            return self.prices[symbol]
        
        return None
    
    def get_status(self) -> Dict:
        """Get service health status"""
        return {
            "state": self.state.value,
            "is_running": self.is_running,
            "source": self.current_source,
            "prices_cached": len(self.prices),
            "last_update": self.last_update.isoformat(),
            "last_successful_update": self.last_successful_update.isoformat(),
            "reconnect_attempt": self.reconnect_attempt,
            "uptime_seconds": (datetime.now() - self.last_update).total_seconds(),
        }
    
    # ============================================
    # MAIN STREAMING LOOP
    # ============================================
    
    async def _stream_loop(self) -> None:
        """Main streaming loop with automatic reconnection"""
        while self.is_running:
            try:
                # Determine which source to use
                ws_url = self.COINCAP_WS if self.current_source == "coincap" else self.BINANCE_WS
                
                logger.info(f"🔌 Connecting to {self.current_source}...")
                self._update_state(ConnectionState.CONNECTING)
                
                # Connect to WebSocket
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
                    self.websocket = websocket
                    self._update_state(ConnectionState.CONNECTED)
                    self.reconnect_attempt = 0
                    
                    logger.info(f"✅ Connected to {self.current_source} WebSocket")
                    
                    # Process messages
                    async for message in websocket:
                        if not self.is_running:
                            break
                        
                        await self._process_message(message)
            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"⚠️ {self.current_source} connection closed: {e}")
                self._update_state(ConnectionState.DISCONNECTED)
                
                # Attempt reconnection with backoff
                await self._handle_reconnection()
            
            except Exception as e:
                logger.error(f"❌ Error in price stream: {e}")
                self._update_state(ConnectionState.OFFLINE)
                
                await asyncio.sleep(5)
                await self._handle_reconnection()
    
    async def _process_message(self, message: str) -> None:
        """Process WebSocket message from CoinCap or Binance"""
        try:
            if self.current_source == "coincap":
                await self._process_coincap_message(message)
            else:
                await self._process_binance_message(message)
            
            self.last_successful_update = datetime.now()
        
        except Exception as e:
            logger.warning(f"⚠️ Error processing message: {e}")
    
    async def _process_coincap_message(self, message: str) -> None:
        """
        Process CoinCap WebSocket message
        Format: {"bitcoin":"45000.50","ethereum":"2500.25",...}
        """
        try:
            data = json.loads(message)
            
            for coin_id, price_str in data.items():
                try:
                    price = float(price_str)
                    
                    # Update in-memory cache
                    self.prices[coin_id] = price
                    
                    # Update Redis cache with 30s TTL
                    cache_key = f"crypto:price:{coin_id}"
                    await redis_cache.set(cache_key, str(price), ttl=30)
                    
                    # Also cache by symbol if we have mapping
                    for symbol, mapped_id in self.symbol_mapping.items():
                        if mapped_id == coin_id:
                            symbol_key = f"crypto:price:{symbol.lower()}"
                            await redis_cache.set(symbol_key, str(price), ttl=30)
                
                except (ValueError, TypeError) as e:
                    logger.debug(f"⚠️ Invalid price for {coin_id}: {e}")
            
            self.last_update = datetime.now()
        
        except json.JSONDecodeError as e:
            logger.debug(f"⚠️ Invalid JSON in CoinCap message: {e}")
    
    async def _process_binance_message(self, message: str) -> None:
        """
        Process Binance WebSocket message
        Format: [{"s":"BTCUSDT","c":"45000.50",...}, ...]
        """
        try:
            data = json.loads(message)
            
            if not isinstance(data, list):
                return
            
            for ticker in data:
                try:
                    symbol = ticker.get("s", "")  # e.g., "BTCUSDT"
                    price_str = ticker.get("c")  # close price
                    
                    if not symbol or not price_str:
                        continue
                    
                    # Extract base symbol (remove USDT/BUSD)
                    base_symbol = symbol.replace("USDT", "").replace("BUSD", "").replace("USDC", "")
                    price = float(price_str)
                    
                    # Update caches
                    self.prices[base_symbol] = price
                    cache_key = f"crypto:price:{base_symbol.lower()}"
                    await redis_cache.set(cache_key, str(price), ttl=30)
                
                except (ValueError, KeyError, TypeError) as e:
                    logger.debug(f"⚠️ Error processing Binance ticker: {e}")
            
            self.last_update = datetime.now()
        
        except json.JSONDecodeError as e:
            logger.debug(f"⚠️ Invalid JSON in Binance message: {e}")
    
    # ============================================
    # RECONNECTION & FAILOVER
    # ============================================
    
    async def _handle_reconnection(self) -> None:
        """Handle reconnection with exponential backoff"""
        if not self.is_running:
            return
        
        self.reconnect_attempt += 1
        
        # Calculate backoff
        backoff = min(
            self.base_backoff * (2 ** (self.reconnect_attempt - 1)),
            self.max_backoff
        )
        
        logger.info(
            f"📈 Reconnection attempt {self.reconnect_attempt}/{self.max_reconnect_attempts} "
            f"in {backoff}s (source: {self.current_source})"
        )
        
        self._update_state(ConnectionState.RECONNECTING)
        await asyncio.sleep(backoff)
        
        # If too many attempts on CoinCap, switch to Binance
        if self.reconnect_attempt > 3 and self.current_source == "coincap":
            logger.warning("⚠️ CoinCap failing, switching to Binance")
            self.current_source = "binance"
            self.reconnect_attempt = 0
            self._update_state(ConnectionState.SWITCHING_SOURCE)
    
    async def _fallback_monitor(self) -> None:
        """Monitor for prolonged outages and switch sources if needed"""
        while self.is_running:
            try:
                time_since_update = (datetime.now() - self.last_successful_update).total_seconds()
                
                # If no updates >30s and using CoinCap, switch to Binance
                if (
                    time_since_update > self.fallback_timeout
                    and self.current_source == "coincap"
                    and self.state != ConnectionState.SWITCHING_SOURCE
                ):
                    logger.warning(f"⚠️ No updates for {time_since_update}s, switching to Binance")
                    self.current_source = "binance"
                    self.reconnect_attempt = 0
                    self._update_state(ConnectionState.SWITCHING_SOURCE)
                    
                    if self.websocket:
                        await self.websocket.close()
                
                await asyncio.sleep(10)
            
            except Exception as e:
                logger.warning(f"⚠️ Error in fallback monitor: {e}")
                await asyncio.sleep(10)
    
    # ============================================
    # UTILITIES
    # ============================================
    
    def _update_state(self, new_state: ConnectionState) -> None:
        """Update connection state with logging"""
        if self.state != new_state:
            logger.info(f"🔄 Connection state: {self.state.value} → {new_state.value}")
            self.state = new_state
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        if not self.is_running:
            return False
        
        time_since_update = (datetime.now() - self.last_successful_update).total_seconds()
        return time_since_update < 60  # Healthy if received update in last 60s


# Global service instance
price_stream_service = PriceStreamService()
