"""
Mock Price Service - Simulated Real-Time Price Updates
Provides realistic price movements when external API is unavailable
"""
import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MockPriceService:
    """Generates realistic mock cryptocurrency prices with simulated volatility"""
    
    # Base prices (as of Feb 2026)
    BASE_PRICES = {
        "bitcoin": {"symbol": "BTC", "price": 52000.00, "name": "Bitcoin"},
        "ethereum": {"symbol": "ETH", "price": 2800.00, "name": "Ethereum"},
        "binance-coin": {"symbol": "BNB", "price": 320.00, "name": "BNB"},
        "solana": {"symbol": "SOL", "price": 105.00, "name": "Solana"},
        "xrp": {"symbol": "XRP", "price": 0.52, "name": "XRP"},
        "cardano": {"symbol": "ADA", "price": 0.48, "name": "Cardano"},
        "dogecoin": {"symbol": "DOGE", "price": 0.082, "name": "Dogecoin"},
        "avalanche": {"symbol": "AVAX", "price": 38.50, "name": "Avalanche"},
        "polkadot": {"symbol": "DOT", "price": 7.20, "name": "Polkadot"},
        "chainlink": {"symbol": "LINK", "price": 15.80, "name": "Chainlink"},
        "polygon": {"symbol": "MATIC", "price": 0.92, "name": "Polygon"},
        "litecoin": {"symbol": "LTC", "price": 72.00, "name": "Litecoin"},
        "uniswap": {"symbol": "UNI", "price": 6.50, "name": "Uniswap"},
        "stellar": {"symbol": "XLM", "price": 0.11, "name": "Stellar"},
        "tron": {"symbol": "TRX", "price": 0.10, "name": "TRON"},
        "cosmos": {"symbol": "ATOM", "price": 9.80, "name": "Cosmos"},
    }
    
    def __init__(self):
        self.current_prices = {}
        self.last_changes = {}
        self._initialize_prices()
        logger.info("🎭 Mock price service initialized with realistic price simulation")
    
    def _initialize_prices(self):
        """Initialize prices with base values"""
        for coin_id, data in self.BASE_PRICES.items():
            self.current_prices[coin_id] = {
                "id": coin_id,
                "symbol": data["symbol"],
                "name": data["name"],
                "priceUsd": str(data["price"]),
                "changePercent24Hr": str(random.uniform(-5, 5)),
                "marketCapUsd": str(data["price"] * random.uniform(1e9, 1e11)),
                "volumeUsd24Hr": str(data["price"] * random.uniform(1e8, 1e9)),
            }
            self.last_changes[coin_id] = 0.0
    
    def get_prices(self) -> Dict[str, Any]:
        """
        Get current prices with simulated real-time changes
        Simulates realistic market volatility
        """
        for coin_id in self.current_prices:
            current_price = float(self.current_prices[coin_id]["priceUsd"])
            
            # Simulate price movement (±0.1% to ±0.5% per update)
            volatility = random.uniform(0.0005, 0.005)  # 0.05% to 0.5%
            direction = random.choice([-1, 1])
            
            # Occasional larger movements (10% chance of ±1% move)
            if random.random() < 0.1:
                volatility = random.uniform(0.005, 0.01)  # 0.5% to 1%
            
            price_change = current_price * volatility * direction
            new_price = current_price + price_change
            
            # Ensure price doesn't go negative or too extreme
            new_price = max(new_price, current_price * 0.5)
            new_price = min(new_price, current_price * 1.5)
            
            # Update price
            self.current_prices[coin_id]["priceUsd"] = f"{new_price:.8f}"
            
            # Calculate 24h change (accumulate changes)
            change_percent = (price_change / current_price) * 100
            old_change = float(self.current_prices[coin_id]["changePercent24Hr"])
            
            # Gradually decay the 24h change towards 0 (simulate time passing)
            decayed_change = old_change * 0.98  # 2% decay per update
            new_24h_change = decayed_change + change_percent
            
            # Keep 24h change realistic (-20% to +20%)
            new_24h_change = max(min(new_24h_change, 20), -20)
            
            self.current_prices[coin_id]["changePercent24Hr"] = f"{new_24h_change:.2f}"
        
        return {
            "data": list(self.current_prices.values()),
            "timestamp": datetime.now().isoformat()
        }


# Global instance
mock_price_service = MockPriceService()
