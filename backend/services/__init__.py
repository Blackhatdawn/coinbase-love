"""
Backend microservices for CryptoVault
Real-time price streaming, caching, gas fee calculation, and WebSocket management

Enterprise Features:
- Price streaming via CoinGecko polling
- Connection management with rate limiting
- Metrics and health monitoring
- Graceful shutdown support
"""

from .price_stream import price_stream_service, PriceStreamService
from .gas_fees import gas_fee_service, GasFeeService
from .websocket_manager import (
    enterprise_ws_manager,
    EnterpriseWebSocketManager,
    ConnectionState,
    ConnectionInfo,
    ConnectionMetrics,
    RateLimiter,
)

__all__ = [
    # Price streaming
    "price_stream_service", 
    "PriceStreamService",
    # Gas fees
    "gas_fee_service",
    "GasFeeService",
    # WebSocket management
    "enterprise_ws_manager",
    "EnterpriseWebSocketManager",
    "ConnectionState",
    "ConnectionInfo",
    "ConnectionMetrics",
    "RateLimiter",
]
