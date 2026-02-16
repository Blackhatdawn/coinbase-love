"""
PriceStreamService
Live cryptocurrency price streaming via CoinGecko polling.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List

import httpx

from config import settings

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISABLED = "disabled"


class PriceStreamService:
    TRACKED_IDS: List[str] = [
        "bitcoin", "ethereum", "binancecoin", "solana", "ripple", "cardano", "dogecoin", "polkadot",
        "chainlink", "litecoin", "avalanche-2", "uniswap"
    ]

    def __init__(self):
        self.is_enabled = True
        self.is_running = False
        self.state = ConnectionState.DISCONNECTED

        self.prices: Dict[str, float] = {}
        self.last_update = datetime.utcnow()
        self.last_successful_update = None

        self.current_source = "coingecko"
        self.reconnect_attempt = 0
        self.error_count = 0

        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        self.base_url = "https://api.coingecko.com/api/v3"
        self.update_interval = 15
        self.timeout = 15

        self.id_to_symbol = {
            "bitcoin": "BTC", "ethereum": "ETH", "binancecoin": "BNB", "solana": "SOL",
            "ripple": "XRP", "cardano": "ADA", "dogecoin": "DOGE", "polkadot": "DOT",
            "chainlink": "LINK", "litecoin": "LTC", "avalanche-2": "AVAX", "uniswap": "UNI"
        }

    async def start(self) -> None:
        if not self.is_enabled:
            self.state = ConnectionState.DISABLED
            return
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self._update_state(ConnectionState.CONNECTING)
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("✅ Starting PriceStreamService (CoinGecko polling)")

    async def stop(self) -> None:
        self.is_running = False
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._update_state(ConnectionState.DISCONNECTED)

    async def health_check(self) -> bool:
        if not self.is_enabled:
            return False
        if not self.last_successful_update:
            return False
        return (datetime.utcnow() - self.last_successful_update).total_seconds() <= 120

    def get_price(self, symbol: str) -> Optional[float]:
        key = (symbol or "").lower()
        return self.prices.get(key)

    def get_all_prices(self) -> Dict[str, float]:
        return self.prices.copy()

    def get_status(self) -> Dict:
        return {
            "enabled": self.is_enabled,
            "state": self.state.value,
            "source": self.current_source,
            "is_running": self.is_running,
            "prices_cached": len(self.prices),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "last_successful_update": self.last_successful_update.isoformat() if self.last_successful_update else None,
            "reconnect_attempt": self.reconnect_attempt,
            "error_count": self.error_count,
        }

    async def _poll_loop(self) -> None:
        while self.is_running and not self._stop_event.is_set():
            try:
                await self._fetch_once()
                self.reconnect_attempt = 0
                self._update_state(ConnectionState.CONNECTED)
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                self.reconnect_attempt += 1
                self._update_state(ConnectionState.RECONNECTING)
                logger.error("❌ PriceStream polling error: %s", str(e))
                await asyncio.sleep(min(30, 2 * self.reconnect_attempt))

    async def _fetch_once(self) -> None:
        params = {
            "vs_currency": "usd",
            "ids": ",".join(self.TRACKED_IDS),
            "order": "market_cap_desc",
            "per_page": len(self.TRACKED_IDS),
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/coins/markets", params=params)
            response.raise_for_status()
            data = response.json()

        next_prices: Dict[str, float] = {}
        for item in data:
            coin_id = item.get("id", "").lower()
            symbol = (item.get("symbol") or "").lower()
            price = float(item.get("current_price") or 0)
            if price <= 0:
                continue
            next_prices[coin_id] = price
            next_prices[symbol] = price

        if next_prices:
            self.prices = next_prices
            self.last_update = datetime.utcnow()
            self.last_successful_update = self.last_update

    def _update_state(self, new_state: ConnectionState) -> None:
        if self.state != new_state:
            logger.info("🔄 Connection state: %s → %s", self.state.value, new_state.value)
            self.state = new_state


price_stream_service = PriceStreamService()
