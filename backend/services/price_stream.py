"""
Production-grade real-time crypto price stream service.

Architecture:
Exchange WebSocket streams (Binance/Kraken/Coinbase) -> centralized cache -> internal consumers.
CoinGecko is used for low-frequency metadata.
CoinMarketCap is used as fallback provider.
Redis caching for top coins market data with 45s TTL.
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

import httpx
import websockets

from config import settings
from redis_cache import redis_cache
from services.circuit_breaker import CircuitBreaker, CircuitState

logger = logging.getLogger(__name__)

PriceCallback = Callable[[Dict[str, float], float], Awaitable[None]]

# Max retry limit for WebSocket reconnections before backing off significantly
MAX_WS_RETRIES = 50
# Scheduled refresh interval for market data (seconds)
MARKET_DATA_REFRESH_INTERVAL = 45


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISABLED = "disabled"


@dataclass
class PriceTick:
    symbol: str
    price: float
    ts_ms: int
    source: str


class TokenBucketRateLimiter:
    """Simple async token bucket limiter for upstream HTTP protection."""

    def __init__(self, rate_per_second: float, capacity: float):
        self.rate = rate_per_second
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: float = 1.0) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = max(0.0, now - self.last_refill)
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens < tokens:
                return False
            self.tokens -= tokens
            return True


class PriceCache:
    """Centralized cache with atomic updates, monotonic timestamp checks, and Redis backing."""

    def __init__(self, live_ttl_seconds: int = 5):
        self.live_ttl_seconds = live_ttl_seconds
        self._lock = asyncio.Lock()
        self._prices: Dict[str, float] = {}
        self._timestamps_ms: Dict[str, int] = {}
        self.last_update = datetime.now(timezone.utc)

    async def update_tick(self, tick: PriceTick) -> bool:
        """Atomic price update, ignoring older ticks for same symbol."""
        async with self._lock:
            current_ts = self._timestamps_ms.get(tick.symbol, 0)
            if tick.ts_ms < current_ts:
                return False

            self._prices[tick.symbol] = tick.price
            self._timestamps_ms[tick.symbol] = tick.ts_ms
            self.last_update = datetime.now(timezone.utc)

            payload = {
                "symbol": tick.symbol,
                "price": tick.price,
                "timestamp_ms": tick.ts_ms,
                "source": tick.source,
            }
            await redis_cache.set(f"crypto:price:{tick.symbol}", payload, ttl=self.live_ttl_seconds)
            return True

    async def snapshot(self) -> Dict[str, float]:
        async with self._lock:
            return dict(self._prices)

    async def get_price(self, symbol: str) -> Optional[float]:
        normalized = symbol.lower()
        async with self._lock:
            val = self._prices.get(normalized)
            ts = self._timestamps_ms.get(normalized)

        if val is not None and ts is not None:
            age_ms = int(time.time() * 1000) - ts
            if age_ms <= self.live_ttl_seconds * 1000:
                return val
        return None

    async def count(self) -> int:
        async with self._lock:
            return len(self._prices)


class PriceStreamService:
    TRACKED_SYMBOLS: List[str] = [
        "BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "XRPUSD", "ADAUSD",
        "DOGEUSD", "DOTUSD", "LINKUSD", "LTCUSD", "AVAXUSD", "UNIUSD",
    ]

    SYMBOL_ALIASES: Dict[str, str] = {
        "XBTUSD": "BTCUSD", "BTCUSDT": "BTCUSD", "ETHUSDT": "ETHUSD",
        "BNBUSDT": "BNBUSD", "SOLUSDT": "SOLUSD", "XRPUSDT": "XRPUSD",
        "ADAUSDT": "ADAUSD", "DOGEUSDT": "DOGEUSD", "DOTUSDT": "DOTUSD",
        "LINKUSDT": "LINKUSD", "LTCUSDT": "LTCUSD", "AVAXUSDT": "AVAXUSD",
        "UNIUSDT": "UNIUSD",
    }

    # CoinGecko ID mapping for metadata
    COINGECKO_IDS = [
        "bitcoin", "ethereum", "binancecoin", "solana", "ripple", "cardano",
        "dogecoin", "polkadot", "chainlink", "litecoin", "avalanche-2", "uniswap",
    ]

    # CoinMarketCap slug mapping
    CMC_SLUGS = {
        "bitcoin": "BTC", "ethereum": "ETH", "binancecoin": "BNB",
        "solana": "SOL", "ripple": "XRP", "cardano": "ADA",
        "dogecoin": "DOGE", "polkadot": "DOT", "chainlink": "LINK",
        "litecoin": "LTC", "avalanche-2": "AVAX", "uniswap": "UNI",
    }

    def __init__(self):
        self.is_enabled = True
        self.is_running = False
        self.state = ConnectionState.DISCONNECTED

        self.cache = PriceCache(live_ttl_seconds=5)
        self.prices: Dict[str, float] = {}
        self.last_update = datetime.now(timezone.utc)
        self.last_successful_update: Optional[datetime] = None

        self.current_source = "exchange_ws"
        self.reconnect_attempt = 0
        self.error_count = 0

        self.message_count = 0
        self.reconnect_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.rate_limit_errors = 0
        self.stream_silence_alerts = 0

        self._last_message_monotonic = time.monotonic()
        self._tasks: List[asyncio.Task] = []
        self._stop_event = asyncio.Event()
        self._callbacks: Set[PriceCallback] = set()
        self._metadata_single_flight = asyncio.Lock()
        self._gecko_rate_limiter = TokenBucketRateLimiter(rate_per_second=1 / 30.0, capacity=2.0)
        self._gecko_circuit_breaker = CircuitBreaker(
            name="coingecko_metadata",
            failure_threshold=5,
            recovery_timeout=90,
            expected_exception=Exception,
        )
        self._cmc_circuit_breaker = CircuitBreaker(
            name="coinmarketcap",
            failure_threshold=5,
            recovery_timeout=120,
            expected_exception=Exception,
        )

        # Track per-exchange retry counts for max retry limit
        self._exchange_retries: Dict[str, int] = {}

    async def start(self) -> None:
        if not self.is_enabled:
            self.state = ConnectionState.DISABLED
            return
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self._update_state(ConnectionState.CONNECTING)

        self._tasks = [
            asyncio.create_task(self._run_exchange_loop("binance")),
            asyncio.create_task(self._run_exchange_loop("kraken")),
            asyncio.create_task(self._run_exchange_loop("coinbase")),
            asyncio.create_task(self._silence_watchdog()),
            asyncio.create_task(self._scheduled_market_data_refresh()),
            asyncio.create_task(self._sync_prices_snapshot_loop()),
        ]
        logger.info("Starting PriceStreamService (exchange websockets + scheduled market data refresh)")

    async def stop(self) -> None:
        self.is_running = False
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.debug("Task stop error: %s", exc)
        self._tasks = []
        self._update_state(ConnectionState.DISCONNECTED)

    async def health_check(self) -> bool:
        """Check if price stream is healthy. Does NOT call external APIs."""
        if not self.is_enabled:
            return False
        if not self.last_successful_update:
            return False
        age = (datetime.now(timezone.utc) - self.last_successful_update).total_seconds()
        return age <= 120  # Consider healthy if update within last 2 minutes

    async def get_cache_freshness(self) -> dict:
        """Return cache freshness info for readiness checks without calling external APIs."""
        cached_markets = await redis_cache.get("crypto:metadata:markets")
        return {
            "has_cached_data": cached_markets is not None,
            "last_successful_update": self.last_successful_update.isoformat() if self.last_successful_update else None,
            "prices_cached": len(self.prices),
            "stream_state": self.state.value,
        }

    def get_price(self, symbol: str) -> Optional[float]:
        return self.prices.get((symbol or "").lower())

    def get_all_prices(self) -> Dict[str, float]:
        return self.prices.copy()

    def subscribe(self, callback: PriceCallback) -> None:
        self._callbacks.add(callback)

    def unsubscribe(self, callback: PriceCallback) -> None:
        self._callbacks.discard(callback)

    async def _notify_subscribers(self, updates: Dict[str, float], timestamp_ms: int) -> None:
        if not updates or not self._callbacks:
            return
        for callback in list(self._callbacks):
            try:
                await callback(updates, timestamp_ms)
            except Exception as exc:
                logger.debug("Subscriber callback failed: %s", exc)

    def get_status(self) -> Dict[str, Any]:
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
            "metrics": {
                "message_rate_total": self.message_count,
                "reconnect_count": self.reconnect_count,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "rate_limit_errors": self.rate_limit_errors,
                "stream_silence_alerts": self.stream_silence_alerts,
            },
        }

    # =========================================================================
    # EXCHANGE WEBSOCKET LOOPS WITH JITTER BACKOFF + MAX RETRY LIMIT
    # =========================================================================

    async def _run_exchange_loop(self, exchange: str) -> None:
        """Run exchange WS loop with exponential backoff + jitter and max retry limit."""
        backoff_seconds = 1.0
        retry_count = 0
        self._exchange_retries[exchange] = 0

        while self.is_running and not self._stop_event.is_set():
            # Check max retry limit
            if retry_count >= MAX_WS_RETRIES:
                logger.error(
                    "%s WS max retry limit (%d) reached. Pausing for 5 minutes before resuming.",
                    exchange, MAX_WS_RETRIES
                )
                await asyncio.sleep(300)  # 5 minute cooldown
                retry_count = 0
                backoff_seconds = 1.0

            try:
                self._update_state(
                    ConnectionState.CONNECTING if retry_count == 0 else ConnectionState.RECONNECTING
                )
                await self._connect_and_consume(exchange)
                # If we get here cleanly, reset backoff
                backoff_seconds = 1.0
                retry_count = 0
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.error_count += 1
                retry_count += 1
                self.reconnect_attempt += 1
                self.reconnect_count += 1
                self._exchange_retries[exchange] = retry_count
                self._update_state(ConnectionState.RECONNECTING)

                # Exponential backoff with random jitter (0-1 second)
                jitter = random.uniform(0, 1.0)
                wait = min(60.0, backoff_seconds + jitter)

                # Log clearly when HTTP 451 (geo-blocked) occurs
                exc_str = str(exc)
                if "451" in exc_str:
                    logger.warning(
                        "%s WS geo-blocked (HTTP 451). Retry %d/%d in %.2fs. "
                        "This region may be restricted by %s.",
                        exchange, retry_count, MAX_WS_RETRIES, wait, exchange
                    )
                else:
                    logger.warning(
                        "%s WS disconnected (%s). Retry %d/%d in %.2fs",
                        exchange, exc, retry_count, MAX_WS_RETRIES, wait
                    )

                await asyncio.sleep(wait)
                backoff_seconds = min(60.0, backoff_seconds * 2)

    async def _connect_and_consume(self, exchange: str) -> None:
        if exchange == "binance":
            await self._consume_binance()
        elif exchange == "kraken":
            await self._consume_kraken()
        elif exchange == "coinbase":
            await self._consume_coinbase()
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    async def _consume_binance(self) -> None:
        stream_names = "/".join(
            f"{s.replace('USD', 'USDT').lower()}@trade" for s in self.TRACKED_SYMBOLS
        )
        url = f"wss://stream.binance.com:9443/stream?streams={stream_names}"

        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_queue=1024) as ws:
            self._update_state(ConnectionState.CONNECTED)
            self._exchange_retries["binance"] = 0  # Reset on successful connect
            async for raw in ws:
                payload = json.loads(raw)
                data = payload.get("data", {})
                symbol = self._normalize_symbol(data.get("s", ""))
                if not symbol:
                    continue
                price = float(data.get("p") or 0)
                if price <= 0:
                    continue
                ts_ms = int(data.get("E") or int(time.time() * 1000))
                await self._handle_tick(PriceTick(symbol=symbol, price=price, ts_ms=ts_ms, source="binance"))

    async def _consume_kraken(self) -> None:
        url = "wss://ws.kraken.com"
        pairs = [
            f"{s.replace('USD', '')}/USD" if not s.startswith("BTC") else "XBT/USD"
            for s in self.TRACKED_SYMBOLS
        ]
        pair_map = {"XBT/USD": "BTCUSD"}
        for s in self.TRACKED_SYMBOLS:
            if s == "BTCUSD":
                continue
            pair_map[f"{s.replace('USD', '')}/USD"] = s

        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_queue=1024) as ws:
            subscribe = {"event": "subscribe", "pair": pairs, "subscription": {"name": "ticker"}}
            await ws.send(json.dumps(subscribe))
            self._update_state(ConnectionState.CONNECTED)
            self._exchange_retries["kraken"] = 0

            async for raw in ws:
                msg = json.loads(raw)
                if isinstance(msg, dict):
                    continue
                if not isinstance(msg, list) or len(msg) < 4:
                    continue
                ticker = msg[1]
                pair = msg[-1]
                symbol = pair_map.get(pair)
                if not symbol:
                    continue
                close_arr = ticker.get("c") if isinstance(ticker, dict) else None
                if not close_arr:
                    continue
                price = float(close_arr[0])
                if price <= 0:
                    continue
                ts_ms = int(time.time() * 1000)
                await self._handle_tick(PriceTick(symbol=symbol, price=price, ts_ms=ts_ms, source="kraken"))

    async def _consume_coinbase(self) -> None:
        url = "wss://advanced-trade-ws.coinbase.com"
        products = [f"{s.replace('USD', '')}-USD" for s in self.TRACKED_SYMBOLS]

        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_queue=1024) as ws:
            subscribe = {
                "type": "subscribe",
                "channel": "ticker",
                "product_ids": products,
            }
            await ws.send(json.dumps(subscribe))
            self._update_state(ConnectionState.CONNECTED)
            self._exchange_retries["coinbase"] = 0

            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("channel") != "ticker":
                    continue
                events = msg.get("events") or []
                for evt in events:
                    for ticker in evt.get("tickers", []):
                        symbol = self._normalize_symbol(ticker.get("product_id", ""))
                        if not symbol:
                            continue
                        price = float(ticker.get("price") or 0)
                        if price <= 0:
                            continue
                        ts_ms = int(time.time() * 1000)
                        await self._handle_tick(
                            PriceTick(symbol=symbol, price=price, ts_ms=ts_ms, source="coinbase")
                        )

    async def _handle_tick(self, tick: PriceTick) -> None:
        updated = await self.cache.update_tick(tick)
        self._last_message_monotonic = time.monotonic()
        self.message_count += 1

        if updated:
            self.last_update = datetime.now(timezone.utc)
            self.last_successful_update = self.last_update
            self.current_source = tick.source
            await self._notify_subscribers({tick.symbol.lower(): tick.price}, tick.ts_ms)

    async def _sync_prices_snapshot_loop(self) -> None:
        while self.is_running and not self._stop_event.is_set():
            self.prices = {k.lower(): v for k, v in (await self.cache.snapshot()).items()}
            await asyncio.sleep(0.25)

    async def _silence_watchdog(self) -> None:
        while self.is_running and not self._stop_event.is_set():
            elapsed = time.monotonic() - self._last_message_monotonic
            if elapsed > 10:
                self.stream_silence_alerts += 1
                logger.warning("Stream silence detected: %.2fs without messages", elapsed)
            await asyncio.sleep(5)

    # =========================================================================
    # SCHEDULED MARKET DATA REFRESH (replaces aggressive CoinGecko polling)
    # Tries CoinGecko -> CoinMarketCap -> returns cached data if both fail
    # =========================================================================

    async def _scheduled_market_data_refresh(self) -> None:
        """Refresh market data on a fixed schedule (every 45s) with jitter."""
        # Initial delay to let WS streams start
        await asyncio.sleep(5)

        while self.is_running and not self._stop_event.is_set():
            try:
                await self._fetch_market_data_with_fallback()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Scheduled market data refresh failed: %s", exc)

            # Wait for next scheduled refresh with jitter
            jitter = random.uniform(0, 10)
            await asyncio.sleep(MARKET_DATA_REFRESH_INTERVAL + jitter)

    async def _fetch_market_data_with_fallback(self) -> None:
        """
        Fetch market data with fallback chain:
        1. CoinGecko (primary)
        2. CoinMarketCap (fallback)
        3. Cached data (last resort)
        """
        # Try CoinGecko first
        gecko_success = await self._try_coingecko_market_data()
        if gecko_success:
            return

        # Fallback to CoinMarketCap
        cmc_success = await self._try_coinmarketcap_market_data()
        if cmc_success:
            return

        # Both failed - check if we have cached data
        cached = await redis_cache.get("crypto:metadata:markets")
        if cached:
            self.cache_hits += 1
            logger.info("Using cached market data (both CoinGecko and CoinMarketCap unavailable)")
        else:
            self.cache_misses += 1
            logger.warning("No market data available - all providers failed and no cache")

    async def _try_coingecko_market_data(self) -> bool:
        """Attempt to fetch market data from CoinGecko. Returns True on success."""
        async with self._metadata_single_flight:
            allowed = await self._gecko_rate_limiter.consume(1)
            if not allowed:
                self.rate_limit_errors += 1
                logger.debug("CoinGecko rate limiter blocked")
                return False

            if self._gecko_circuit_breaker.state == CircuitState.OPEN:
                logger.debug("CoinGecko circuit open, skipping")
                return False

            backoff = 1.0
            for attempt in range(3):
                try:
                    async with httpx.AsyncClient(timeout=12) as client:
                        resp = await client.get(
                            "https://api.coingecko.com/api/v3/coins/markets",
                            params={
                                "vs_currency": "usd",
                                "ids": ",".join(self.COINGECKO_IDS),
                                "order": "market_cap_desc",
                                "per_page": len(self.COINGECKO_IDS),
                                "page": 1,
                                "sparkline": "false",
                                "price_change_percentage": "24h",
                            },
                        )

                    if resp.status_code == 429:
                        self.rate_limit_errors += 1
                        self._gecko_circuit_breaker._record_failure()
                        jitter = random.uniform(0.1, 1.0)
                        wait = min(60.0, backoff + jitter)
                        logger.warning("CoinGecko 429, backing off %.2fs (attempt %d)", wait, attempt + 1)
                        await asyncio.sleep(wait)
                        backoff *= 2
                        continue

                    resp.raise_for_status()
                    self._gecko_circuit_breaker._record_success()
                    data = resp.json()
                    # Cache with 45-second TTL
                    await redis_cache.set("crypto:metadata:markets", data, ttl=45)
                    logger.debug("CoinGecko market data refreshed and cached (45s TTL)")
                    return True

                except httpx.HTTPStatusError:
                    self._gecko_circuit_breaker._record_failure()
                    break
                except Exception as exc:
                    self._gecko_circuit_breaker._record_failure()
                    logger.debug("CoinGecko request failed: %s", exc)
                    break

        return False

    async def _try_coinmarketcap_market_data(self) -> bool:
        """
        Attempt to fetch market data from CoinMarketCap free tier.
        Requires COINMARKETCAP_API_KEY env var.
        Free tier: 30 requests/minute.
        Returns True on success.
        """
        cmc_api_key = getattr(settings, "coinmarketcap_api_key", None)
        if not cmc_api_key:
            logger.debug("CoinMarketCap API key not configured, skipping fallback")
            return False

        if self._cmc_circuit_breaker.state == CircuitState.OPEN:
            logger.debug("CoinMarketCap circuit open, skipping")
            return False

        try:
            symbols = ",".join(self.CMC_SLUGS.values())
            async with httpx.AsyncClient(timeout=12) as client:
                resp = await client.get(
                    "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                    params={"symbol": symbols, "convert": "USD"},
                    headers={"X-CMC_PRO_API_KEY": cmc_api_key},
                )

            if resp.status_code == 429:
                self.rate_limit_errors += 1
                self._cmc_circuit_breaker._record_failure()
                logger.warning("CoinMarketCap 429 rate limit hit")
                return False

            resp.raise_for_status()
            self._cmc_circuit_breaker._record_success()
            data = resp.json()

            # Transform CMC data to match CoinGecko format for cache compatibility
            cmc_data = data.get("data", {})
            market_data = []
            for gecko_id, cmc_symbol in self.CMC_SLUGS.items():
                coin_data = cmc_data.get(cmc_symbol)
                if coin_data:
                    quote = coin_data.get("quote", {}).get("USD", {})
                    market_data.append({
                        "id": gecko_id,
                        "symbol": cmc_symbol.lower(),
                        "name": coin_data.get("name", ""),
                        "current_price": quote.get("price", 0),
                        "market_cap": quote.get("market_cap", 0),
                        "price_change_percentage_24h": quote.get("percent_change_24h", 0),
                        "source": "coinmarketcap",
                    })

            if market_data:
                await redis_cache.set("crypto:metadata:markets", market_data, ttl=45)
                logger.info("CoinMarketCap market data refreshed and cached (45s TTL)")
                return True

        except Exception as exc:
            self._cmc_circuit_breaker._record_failure()
            logger.warning("CoinMarketCap request failed: %s", exc)

        return False

    def _normalize_symbol(self, raw_symbol: str) -> Optional[str]:
        if not raw_symbol:
            return None
        symbol = raw_symbol.upper().replace("-", "").replace("/", "")
        symbol = self.SYMBOL_ALIASES.get(symbol, symbol)
        if symbol in self.TRACKED_SYMBOLS:
            return symbol
        return None

    def _update_state(self, new_state: ConnectionState) -> None:
        if self.state != new_state:
            logger.info("Connection state: %s -> %s", self.state.value, new_state.value)
            self.state = new_state


price_stream_service = PriceStreamService()
