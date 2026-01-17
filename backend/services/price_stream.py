"""
PriceStreamService
Real-time cryptocurrency price streaming service.
Connects to CoinCap WebSocket for specific assets only.

Architecture:
1. Connect to CoinCap WebSocket (primary source) - SPECIFIC ASSETS ONLY
2. Parse JSON stream and update in-memory cache
3. Auto-reconnect on disconnect with exponential backoff
4. Fallback to cached data if connection fails
5. Monitor connection health with detailed logging
"""

import asyncio
import json
import logging
import time
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

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
    Connects to CoinCap WebSocket for specific tracked assets only.
    """
    
    # Track only major coins to reduce message volume
    TRACKED_ASSETS = [
        "bitcoin", "ethereum", "binancecoin", "solana", 
        "ripple", "cardano", "dogecoin", "polkadot",
        "chainlink", "litecoin", "avalanche-2", "polygon"
    ]
    
    def __init__(self):
        # Connection management
        self.state = ConnectionState.DISCONNECTED
        self.is_running = False
        self.websocket = None
        
        # Reconnection strategy - INCREASED BACKOFF
        self.reconnect_attempt = 0
        self.max_reconnect_attempts = 5
        self.base_backoff = 5  # Start at 5 seconds (was 1)
        self.max_backoff = 120  # Max 2 minutes (was 30)
        self.min_reconnect_interval = 10  # Minimum 10 seconds between reconnects
        self.last_reconnect_time = 0
        
        # WebSocket endpoint - SPECIFIC ASSETS ONLY
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
        self._health_task: Optional[asyncio.Task] = None
        
        if not WEBSOCKETS_AVAILABLE:
            self.state = ConnectionState.DISABLED
            logger.warning("🚫 PriceStreamService disabled - websockets not available")
        else:
            logger.info("🚀 PriceStreamService initialized (tracking %d assets)", len(self.TRACKED_ASSETS))
    
    # ============================================
    # LIFECYCLE METHODS
    # ============================================
    
    async def start(self) -> None:
        """Start the price stream service"""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("⚠️ Cannot start - websockets library not available")
            return
        
        if self.is_running:
            logger.warning("⚠️ PriceStreamService already running")
            return
        
        self.is_running = True
        self.reconnect_attempt = 0
        
        logger.info("✅ Starting PriceStreamService")
        self._task = asyncio.create_task(self._stream_loop())
        self._health_task = asyncio.create_task(self._health_monitor())
    
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
        
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        self._update_state(ConnectionState.DISCONNECTED)
        logger.info("🛑 PriceStreamService stopped")
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        # Check by coin ID first
        if symbol.lower() in self.prices:
            return self.prices[symbol.lower()]
        
        # Check by symbol
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
            "state": self.state.value,
            "is_running": self.is_running,
            "prices_cached": len(self.prices),
            "last_update": self.last_update.isoformat(),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "reconnect_attempt": self.reconnect_attempt,
        }
    
    # ============================================
    # MAIN STREAMING LOOP
    # ============================================
    
    async def _stream_loop(self) -> None:
        """Main streaming loop with automatic reconnection"""
        while self.is_running:
            try:
                # Enforce minimum reconnect interval
                time_since_last = time.time() - self.last_reconnect_time
                if time_since_last < self.min_reconnect_interval:
                    wait_time = self.min_reconnect_interval - time_since_last
                    logger.debug(f"⏳ Waiting {wait_time:.1f}s before reconnect...")
                    await asyncio.sleep(wait_time)
                
                self.last_reconnect_time = time.time()
                
                logger.info("🔌 Connecting to CoinCap WebSocket...")
                self._update_state(ConnectionState.CONNECTING)
                
                # Connect to WebSocket with proper settings
                async with websockets.connect(
                    self.COINCAP_WS,
                    ping_interval=30,  # Increased from 20
                    ping_timeout=15,   # Increased from 10
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,  # 10MB max message
                ) as websocket:
                    self.websocket = websocket
                    self._update_state(ConnectionState.CONNECTED)
                    self.reconnect_attempt = 0
                    
                    logger.info("✅ Connected to CoinCap WebSocket")
                    
                    # Process messages
                    async for message in websocket:
                        if not self.is_running:
                            break
                        
                        await self._process_message(message)
            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"⚠️ WebSocket connection closed: {e.code} - {e.reason}")
                self._update_state(ConnectionState.DISCONNECTED)
                await self._handle_reconnection()
            
            except websockets.exceptions.InvalidStatusCode as e:
                logger.error(f"❌ WebSocket invalid status: {e}")
                self.error_count += 1
                await self._handle_reconnection()
            
            except asyncio.TimeoutError:
                logger.warning("⚠️ WebSocket connection timeout")
                self._update_state(ConnectionState.DISCONNECTED)
                await self._handle_reconnection()
            
            except Exception as e:
                logger.error(f"❌ Error in price stream: {type(e).__name__}: {e}")
                self.error_count += 1
                self._update_state(ConnectionState.DISCONNECTED)
                await self._handle_reconnection()
    
    async def _process_message(self, message: str) -> None:
        """Process WebSocket message from CoinCap"""
        try:
            data = json.loads(message)
            
            for coin_id, price_str in data.items():
                try:
                    price = float(price_str)
                    self.prices[coin_id] = price
                except (ValueError, TypeError):
                    continue
            
            self.last_update = datetime.now()
            self.last_message_time = datetime.now()
            self.message_count += 1
        
        except json.JSONDecodeError as e:
            logger.debug(f"⚠️ Invalid JSON: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Error processing message: {e}")
    
    # ============================================
    # RECONNECTION
    # ============================================
    
    async def _handle_reconnection(self) -> None:
        """Handle reconnection with exponential backoff"""
        if not self.is_running:
            return
        
        self.reconnect_attempt += 1
        
        if self.reconnect_attempt > self.max_reconnect_attempts:
            logger.error(f"❌ Max reconnection attempts ({self.max_reconnect_attempts}) exceeded. Stopping.")
            self.is_running = False
            self._update_state(ConnectionState.DISABLED)
            return
        
        # Calculate backoff with exponential increase
        backoff = min(
            self.base_backoff * (2 ** (self.reconnect_attempt - 1)),
            self.max_backoff
        )
        
        logger.info(
            f"📈 Reconnection attempt {self.reconnect_attempt}/{self.max_reconnect_attempts} "
            f"in {backoff}s"
        )
        
        self._update_state(ConnectionState.RECONNECTING)
        await asyncio.sleep(backoff)
    
    async def _health_monitor(self) -> None:
        """Monitor connection health"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if self.state == ConnectionState.CONNECTED:
                    time_since_message = (datetime.now() - self.last_message_time).total_seconds()
                    
                    if time_since_message > 120:  # No message in 2 minutes
                        logger.warning(f"⚠️ No messages received for {time_since_message:.0f}s - connection may be stale")
                        
                        # Force reconnect if stale
                        if self.websocket:
                            await self.websocket.close()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"⚠️ Health monitor error: {e}")
    
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
        
        if self.state != ConnectionState.CONNECTED:
            return False
        
        time_since_update = (datetime.now() - self.last_update).total_seconds()
        return time_since_update < 120  # Healthy if received update in last 2 minutes


# Global service instance
price_stream_service = PriceStreamService()
