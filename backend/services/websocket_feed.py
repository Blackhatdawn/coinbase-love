"""
WebSocket Price Feed Service
Real-time cryptocurrency price updates via CoinGecko polling.
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
    def __init__(self):
        self.connections: Set = set()
        self.prices: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.last_api_call: Optional[datetime] = None

        self.update_interval = 15
        self.min_api_interval = 5
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.backoff_multiplier = 1
        self._dns_warning_logged = False

        self.tracked_coins = [
            "bitcoin", "ethereum", "binancecoin", "solana", "ripple", "cardano", "dogecoin", "avalanche-2",
            "polkadot", "chainlink", "matic-network", "litecoin", "uniswap", "stellar", "tron", "cosmos"
        ]

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._price_update_loop())
        logger.info("📡 Price feed started (CoinGecko API, interval: %ds)", self.update_interval)

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("📡 Price feed stopped")

    def add_connection(self, websocket):
        self.connections.add(websocket)

    def remove_connection(self, websocket):
        self.connections.discard(websocket)

    async def _fetch_prices(self) -> Dict[str, Any]:
        if getattr(settings, 'use_mock_prices', False):
            from services.mock_prices import mock_price_service
            return mock_price_service.get_prices()

        if self.last_api_call:
            elapsed = (datetime.now() - self.last_api_call).total_seconds()
            if elapsed < self.min_api_interval:
                await asyncio.sleep(self.min_api_interval - elapsed)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": ",".join(self.tracked_coins),
                        "order": "market_cap_desc",
                        "per_page": len(self.tracked_coins),
                        "page": 1,
                        "sparkline": "false",
                        "price_change_percentage": "24h",
                    },
                )
            self.last_api_call = datetime.now()
            response.raise_for_status()
            self.consecutive_errors = 0
            self.backoff_multiplier = 1
            data = response.json()
            return {"data": data}
        except httpx.ConnectError as e:
            if not self._dns_warning_logged:
                logger.warning("🌐 CoinGecko connect error (%s). Using mock prices.", str(e))
                self._dns_warning_logged = True
            from services.mock_prices import mock_price_service
            return mock_price_service.get_prices()
        except Exception as e:
            logger.error("❌ Price fetch error: %s", e)
            self.consecutive_errors += 1
            return {}

    async def _price_update_loop(self):
        while self.is_running:
            try:
                if self.consecutive_errors >= self.max_consecutive_errors:
                    await asyncio.sleep(60)
                    self.consecutive_errors = 0
                    self.backoff_multiplier = 1
                    continue

                raw_data = await self._fetch_prices()
                if raw_data and raw_data.get("data"):
                    formatted = self._format_prices(raw_data["data"])
                    changes = self._detect_changes(formatted)
                    self.prices = formatted
                    self.last_update = datetime.utcnow()

                    if self.connections:
                        await self._broadcast({
                            "type": "price_update",
                            "data": formatted,
                            "prices": {k: str(v["price"]) for k, v in formatted.items()},
                            "changes": changes,
                            "source": "coingecko",
                            "timestamp": self.last_update.isoformat(),
                        })

                await asyncio.sleep(self.update_interval * self.backoff_multiplier)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Price update loop error: %s", e)
                await asyncio.sleep(10)

    def _format_prices(self, assets: list) -> Dict[str, Any]:
        formatted = {}
        for asset in assets:
            try:
                symbol = (asset.get("symbol") or "").upper()
                if not symbol:
                    continue
                formatted[symbol.lower()] = {
                    "symbol": symbol,
                    "id": asset.get("id", ""),
                    "name": asset.get("name", ""),
                    "price": float(asset.get("current_price") or 0),
                    "change_24h": float(asset.get("price_change_percentage_24h") or 0),
                    "market_cap": float(asset.get("market_cap") or 0),
                    "volume_24h": float(asset.get("total_volume") or 0),
                    "rank": int(asset.get("market_cap_rank") or 0),
                }
            except (ValueError, TypeError):
                continue
        return formatted

    def _detect_changes(self, new_prices: Dict) -> Dict[str, str]:
        changes = {}
        for symbol, data in new_prices.items():
            old_price = self.prices.get(symbol, {}).get("price", 0)
            new_price = data["price"]
            if old_price > 0:
                changes[symbol] = "up" if new_price > old_price else "down" if new_price < old_price else "unchanged"
        return changes

    async def _broadcast(self, message: Dict):
        if not self.connections:
            return
        data = json.dumps(message)
        disconnected = set()
        for ws in self.connections:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.connections.discard(ws)

    async def send_to_client(self, websocket, message: Dict):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Send to client error: %s", e)

    def get_current_prices(self) -> Dict[str, Any]:
        return {
            "prices": self.prices,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "source": "coingecko",
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "connected_clients": len(self.connections),
            "prices_cached": len(self.prices),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "consecutive_errors": self.consecutive_errors,
            "backoff_multiplier": self.backoff_multiplier,
            "source": "coingecko",
        }


price_feed = PriceFeedManager()
