"""
PriceStreamService
Real-time cryptocurrency price streaming service.

NOTE: CoinCap WebSocket now requires an API key (free tier limited).
This service is DISABLED by default. Use the CoinGecko-based websocket_feed instead.

To enable with CoinCap API key:
1. Get API key from https://coincap.io/api-key
2. Set COINCAP_API_KEY in .env
3. Service will auto-enable
"""

import asyncio
import json
import logging
import time
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

from config import settings

logger = logging.getLogger(__name__)

# Try to import websockets, but gracefully handle if not available
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("⚠️ websockets library not available - price streaming disabled")


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISABLED = "disabled"


class PriceStreamService:
    """
    Real-time price streaming service with automatic failover.
    
    IMPORTANT: CoinCap WebSocket API now requires an API key.
    This service is disabled by default. Set COINCAP_API_KEY in .env to enable.
    """
    
    # Track only major coins
    TRACKED_ASSETS = [
        "bitcoin", "ethereum", "binancecoin", "solana", 
        "ripple", "cardano", "dogecoin", "polkadot",
        "chainlink", "litecoin", "avalanche-2", "polygon"
    ]
    
    def __init__(self):
        # Check for API key
        self.api_key = settings.coincap_api_key
        self.is_enabled = bool(self.api_key) and WEBSOCKETS_AVAILABLE
        
        # Connection management
        self.state = ConnectionState.DISABLED if not self.is_enabled else ConnectionState.DISCONNECTED
        self.is_running = False
        self.websocket = None
        
        # Reconnection strategy
        self.reconnect_attempt = 0
        self.max_reconnect_attempts = 3
        self.base_backoff = 30
        self.max_backoff = 300
        self.last_reconnect_time = 0
        
        # WebSocket endpoint (requires API key header now)
        self.COINCAP_WS = f"wss://ws.coincap.io/prices?assets={','.join(self.TRACKED_ASSETS)}"
        
        # Price tracking
        self.prices: Dict[str, float] = {}
        self.last_update = datetime.now()
        self.last_message_time = datetime.now()
        
        # Symbol mapping
        self.symbol_mapping = {
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
            "litecoin": "LTC",
        }
        
        # Health check
        self.message_count = 0
        self.error_count = 0
        
        # Tasks
        self._task: Optional[asyncio.Task] = None
        
        if not self.is_enabled:
            if not self.api_key:
                logger.info("ℹ️ PriceStreamService disabled - COINCAP_API_KEY not set")
                logger.info("ℹ️ Using CoinGecko API via websocket_feed instead")
            elif not WEBSOCKETS_AVAILABLE:
                logger.warning("⚠️ PriceStreamService disabled - websockets not available")
        else:
            logger.info("🚀 PriceStreamService initialized (tracking %d assets)", len(self.TRACKED_ASSETS))
    
    async def start(self) -> None:
        """Start the price stream service"""
        if not self.is_enabled:
            logger.info("ℹ️ PriceStreamService not starting (disabled)")
            return
        
        if self.is_running:
            logger.warning("⚠️ PriceStreamService already running")
            return
        
        self.is_running = True
        self.reconnect_attempt = 0
        
        logger.info("✅ Starting PriceStreamService (CoinCap WebSocket)")
        self._task = asyncio.create_task(self._stream_loop())
    
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
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._update_state(ConnectionState.DISCONNECTED)
        logger.info("🛑 PriceStreamService stopped")
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if symbol.lower() in self.prices:
            return self.prices[symbol.lower()]
        
        for coin_id, sym in self.symbol_mapping.items():
            if sym.upper() == symbol.upper() and coin_id in self.prices:
                return self.prices[coin_id]
        
        return None
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get all cached prices"""
        return self.prices.copy()
    
    def get_status(self) -> Dict:
        """Get service health status"""
        return {
            "enabled": self.is_enabled,
            "state": self.state.value,
            "is_running": self.is_running,
            "prices_cached": len(self.prices),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "message_count": self.message_count,
            "error_count": self.error_count,
        }
    
    async def _stream_loop(self) -> None:
        """Main streaming loop with automatic reconnection"""
        while self.is_running:
            try:
                # Wait between reconnection attempts
                if self.reconnect_attempt > 0:
                    backoff = min(
                        self.base_backoff * (2 ** (self.reconnect_attempt - 1)),
                        self.max_backoff
                    )
                    logger.info(f"⏳ Reconnecting in {backoff}s (attempt {self.reconnect_attempt}/{self.max_reconnect_attempts})")
                    await asyncio.sleep(backoff)
                
                if self.reconnect_attempt >= self.max_reconnect_attempts:
                    logger.error("❌ Max reconnection attempts reached. Disabling service.")
                    self.is_running = False
                    self._update_state(ConnectionState.DISABLED)
                    break
                
                logger.info("🔌 Connecting to CoinCap WebSocket...")
                self._update_state(ConnectionState.CONNECTING)
                
                # Connect with API key header
                headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                
                async with websockets.connect(
                    self.COINCAP_WS,
                    extra_headers=headers,
                    ping_interval=30,
                    ping_timeout=15,
                    close_timeout=10,
                ) as websocket:
                    self.websocket = websocket
                    self._update_state(ConnectionState.CONNECTED)
                    self.reconnect_attempt = 0
                    
                    logger.info("✅ Connected to CoinCap WebSocket")
                    
                    async for message in websocket:
                        if not self.is_running:
                            break
                        await self._process_message(message)
            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"⚠️ WebSocket closed: {e.code} - {e.reason}")
                self._update_state(ConnectionState.DISCONNECTED)
                self.reconnect_attempt += 1
            
            except Exception as e:
                logger.error(f"❌ WebSocket error: {type(e).__name__}: {e}")
                self.error_count += 1
                self._update_state(ConnectionState.DISCONNECTED)
                self.reconnect_attempt += 1
    
    async def _process_message(self, message: str) -> None:
        """Process WebSocket message"""
        try:
            data = json.loads(message)
            
            # Check for error
            if "error" in data:
                logger.error(f"❌ CoinCap error: {data['error']}")
                return
            
            for coin_id, price_str in data.items():
                try:
                    self.prices[coin_id] = float(price_str)
                except (ValueError, TypeError):
                    continue
            
            self.last_update = datetime.now()
            self.last_message_time = datetime.now()
            self.message_count += 1
        
        except json.JSONDecodeError as e:
            logger.debug(f"⚠️ Invalid JSON: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Error processing message: {e}")
    
    def _update_state(self, new_state: ConnectionState) -> None:
        """Update connection state with logging"""
        if self.state != new_state:
            logger.info(f"🔄 Connection state: {self.state.value} → {new_state.value}")
            self.state = new_state


# Global service instance
price_stream_service = PriceStreamService()
