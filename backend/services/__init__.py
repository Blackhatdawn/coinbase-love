"""
Backend microservices for CryptoVault
Real-time price streaming, caching, and WebSocket management
"""

from .price_stream import price_stream_service, PriceStreamService

__all__ = ["price_stream_service", "PriceStreamService"]
