"""
PriceStreamService
Real-time cryptocurrency price streaming service via CoinCap WebSocket.

CoinCap provides FREE WebSocket access for real-time price data.
An API key is optional but provides higher rate limits.

Configuration:
- COINCAP_API_KEY: Optional API key for higher rate limits
- Service auto-starts when websockets library is available
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
    import websockets.exceptions
    WEBSOCKETS_AVAILABLE = True
    WEBSOCKETS_VERSION = getattr(websockets, '__version__', 'unknown')
    logger.info(f"📦 websockets library version: {WEBSOCKETS_VERSION}")
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WEBSOCKETS_VERSION = None
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
    
    # Track only major coins - using correct CoinCap asset IDs
    # Note: CoinCap uses specific IDs, not all coins use the same ID as their name
    TRACKED_ASSETS = [
        "bitcoin", "ethereum", "tether", "solana", 
        "xrp", "cardano", "dogecoin", "polkadot",
        "chainlink", "litecoin", "avalanche", "matic-network"
    ]
    
    def __init__(self):
        # API key is optional - CoinCap WebSocket works without it
        self.api_key = settings.coincap_api_key
        
        # Service is enabled if websockets library is available
        # API key is optional but provides higher rate limits
        self.is_enabled = WEBSOCKETS_AVAILABLE
        
        # Connection management
        self.state = ConnectionState.DISABLED if not self.is_enabled else ConnectionState.DISCONNECTED
        self.is_running = False
        self.websocket = None
        
        # Reconnection strategy
        self.reconnect_attempt = 0
        self.max_reconnect_attempts = 5
        self.base_backoff = 10
        self.max_backoff = 120
        self.last_reconnect_time = 0
        
        # WebSocket endpoint - CoinCap requires API key via query parameter
        # API key is passed via the 'apiKey' query parameter
        ws_base = settings.coincap_ws_url or "wss://ws.coincap.io/prices"
        assets_param = f"assets={','.join(self.TRACKED_ASSETS)}"
        
        if self.api_key:
            self.COINCAP_WS = f"{ws_base}?{assets_param}&apiKey={self.api_key}"
            logger.info(f"🔑 CoinCap WebSocket configured with API key: {self.api_key[:8]}...")
        else:
            self.COINCAP_WS = f"{ws_base}?{assets_param}"
            logger.warning("⚠️ CoinCap WebSocket configured WITHOUT API key - may be rate limited")
        
        # Price tracking
        self.prices: Dict[str, float] = {}
        self.last_update = datetime.now()
        self.last_message_time = datetime.now()
        
        # Symbol mapping - CoinCap IDs to common symbols
        self.symbol_mapping = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "tether": "USDT",
            "solana": "SOL",
            "xrp": "XRP",
            "cardano": "ADA",
            "dogecoin": "DOGE",
            "avalanche": "AVAX",
            "polkadot": "DOT",
            "chainlink": "LINK",
            "matic-network": "MATIC",
            "litecoin": "LTC",
        }
        
        # Health check
        self.message_count = 0
        self.error_count = 0
        
        # Current data source
        self.current_source = "coincap"
        
        # Authorization tracking
        self._auth_error_received = False
        
        # Tasks
        self._task: Optional[asyncio.Task] = None
        
        if not self.is_enabled:
            logger.warning("⚠️ PriceStreamService disabled - websockets library not available")
        else:
            if self.api_key:
                logger.info("🚀 PriceStreamService initialized with API key (tracking %d assets)", 
                           len(self.TRACKED_ASSETS))
            else:
                logger.warning("⚠️ PriceStreamService initialized WITHOUT API key")
                logger.warning("   CoinCap now requires an API key for WebSocket access.")
                logger.warning("   Get a free API key at: https://coincap.io/api-key")
                logger.warning("   Set COINCAP_API_KEY in your environment to enable real-time prices.")
    
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
        status = {
            "enabled": self.is_enabled,
            "state": self.state.value,
            "source": self.current_source,
            "is_running": self.is_running,
            "prices_cached": len(self.prices),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "message_count": self.message_count,
            "error_count": self.error_count,
        }
        
        # Add auth error info if applicable
        if self._auth_error_received:
            status["auth_error"] = True
            status["auth_message"] = "CoinCap requires API key. Set COINCAP_API_KEY environment variable."
        
        return status
    
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
                
                # Build connection parameters
                # Note: websockets 10.0+ uses 'additional_headers' instead of 'extra_headers'
                connect_kwargs = {
                    "ping_interval": 30,
                    "ping_timeout": 15,
                    "close_timeout": 10,
                }
                
                # Note: CoinCap API key is passed via query parameter, not header
                # Header auth was removed in their latest API version
                
                async with websockets.connect(
                    self.COINCAP_WS,
                    **connect_kwargs
                ) as websocket:
                    self.websocket = websocket
                    self._update_state(ConnectionState.CONNECTED)
                    self.reconnect_attempt = 0
                    
                    logger.info("✅ Connected to CoinCap WebSocket")
                    
                    async for message in websocket:
                        if not self.is_running:
                            break
                        
                        # Process message and check for fatal errors
                        should_continue = await self._process_message(message)
                        
                        if not should_continue:
                            # Fatal error (e.g., auth error) - stop the service
                            logger.error("🛑 Fatal error received from CoinCap - stopping service")
                            self.is_running = False
                            self._update_state(ConnectionState.DISABLED)
                            break
            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"⚠️ WebSocket closed: {e.code} - {e.reason}")
                self._update_state(ConnectionState.DISCONNECTED)
                self.reconnect_attempt += 1
            
            except websockets.exceptions.InvalidStatusCode as e:
                logger.error(f"❌ WebSocket connection rejected: HTTP {e.status_code}")
                self.error_count += 1
                self._update_state(ConnectionState.DISCONNECTED)
                # If we get 401/403, likely API key issue - don't retry as fast
                if e.status_code in (401, 403):
                    logger.warning("⚠️ Authentication error - check COINCAP_API_KEY")
                    self.reconnect_attempt += 2  # Skip ahead to longer backoff
                else:
                    self.reconnect_attempt += 1
            
            except ConnectionRefusedError as e:
                logger.error(f"❌ Connection refused: {e}")
                self.error_count += 1
                self._update_state(ConnectionState.DISCONNECTED)
                self.reconnect_attempt += 1
            
            except asyncio.TimeoutError:
                logger.warning("⚠️ WebSocket connection timeout")
                self._update_state(ConnectionState.DISCONNECTED)
                self.reconnect_attempt += 1
            
            except TypeError as e:
                # Catch API compatibility issues (e.g., wrong parameter names)
                logger.error(f"❌ WebSocket API error (possible version incompatibility): {e}")
                logger.error(f"   websockets version: {WEBSOCKETS_VERSION}")
                self.error_count += 1
                self._update_state(ConnectionState.DISABLED)
                self.is_running = False  # Stop trying if there's an API issue
                break
            
            except Exception as e:
                logger.error(f"❌ WebSocket error: {type(e).__name__}: {e}")
                self.error_count += 1
                self._update_state(ConnectionState.DISCONNECTED)
                self.reconnect_attempt += 1
    
    async def _process_message(self, message: str) -> bool:
        """
        Process WebSocket message.
        
        Returns:
            True if message was processed successfully
            False if a fatal error occurred (should stop the connection)
        """
        try:
            data = json.loads(message)
            
            # Check for error messages from CoinCap
            if "error" in data:
                error_msg = data['error']
                logger.error(f"❌ CoinCap error: {error_msg}")
                
                # Check if this is an authorization error - this is fatal
                if "Unauthorized" in error_msg or "API key" in error_msg.lower():
                    logger.error("🔒 CoinCap requires an API key. Set COINCAP_API_KEY in environment.")
                    logger.info("ℹ️ Get a free API key at https://coincap.io/api-key")
                    self._auth_error_received = True
                    return False  # Signal to stop the connection
                
                self.error_count += 1
                return True  # Non-fatal error, continue listening
            
            # Process price data
            for coin_id, price_str in data.items():
                try:
                    self.prices[coin_id] = float(price_str)
                except (ValueError, TypeError):
                    continue
            
            self.last_update = datetime.now()
            self.last_message_time = datetime.now()
            self.message_count += 1
            return True
        
        except json.JSONDecodeError as e:
            logger.debug(f"⚠️ Invalid JSON: {e}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Error processing message: {e}")
            return True
    
    def _update_state(self, new_state: ConnectionState) -> None:
        """Update connection state with logging"""
        if self.state != new_state:
            logger.info(f"🔄 Connection state: {self.state.value} → {new_state.value}")
            self.state = new_state


# Global service instance
price_stream_service = PriceStreamService()
