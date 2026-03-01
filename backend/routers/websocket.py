"""
WebSocket Endpoints for Real-Time Price Streaming.
Streams cached exchange WebSocket prices to connected clients.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services import price_stream_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


class PriceStreamManager:
    """Manages client WebSockets and non-blocking fan-out from central cache updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.client_queues: Dict[WebSocket, asyncio.Queue] = {}
        self.sender_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.max_queue_size = 200
        self._subscriber_registered = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_queues[websocket] = asyncio.Queue(maxsize=self.max_queue_size)
        self.sender_tasks[websocket] = asyncio.create_task(self._client_sender_loop(websocket))

        if not self._subscriber_registered:
            price_stream_service.subscribe(self.enqueue_price_update)
            self._subscriber_registered = True

        logger.info("📡 WebSocket connected (total: %d)", len(self.active_connections))
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to centralized price cache",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

        sender_task = self.sender_tasks.pop(websocket, None)
        if sender_task:
            sender_task.cancel()

        self.client_queues.pop(websocket, None)

        if not self.active_connections and self._subscriber_registered:
            price_stream_service.unsubscribe(self.enqueue_price_update)
            self._subscriber_registered = False

        logger.info("📡 WebSocket disconnected (total: %d)", len(self.active_connections))

    async def enqueue_price_update(self, prices: Dict[str, float], timestamp_ms: float):
        if not self.active_connections:
            return

        message = {
            "type": "price_update",
            "prices": {k: str(v) for k, v in prices.items()},
            "timestamp": datetime.utcnow().isoformat(),
            "event_timestamp_ms": int(timestamp_ms),
            "source": price_stream_service.current_source,
        }

        disconnected: Set[WebSocket] = set()
        for ws, queue in list(self.client_queues.items()):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # Backpressure protection: drop oldest, keep latest.
                try:
                    _ = queue.get_nowait()
                    queue.put_nowait(message)
                except Exception:
                    disconnected.add(ws)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self.disconnect(ws)

    async def _client_sender_loop(self, websocket: WebSocket):
        queue = self.client_queues[websocket]
        while websocket in self.active_connections:
            try:
                message = await queue.get()
                await websocket.send_json(message)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("Client sender loop error: %s", exc)
                self.disconnect(websocket)
                break


price_stream_manager = PriceStreamManager()


@router.websocket("/ws/prices")
async def websocket_price_stream(websocket: WebSocket):
    await price_stream_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif message_type == "get_status":
                    status = price_stream_service.get_status()
                    await websocket.send_json(
                        {
                            "type": "status",
                            "state": status["state"],
                            "source": status["source"],
                            "prices_cached": status["prices_cached"],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                elif message_type == "get_price":
                    symbol = (message.get("symbol") or "").lower()
                    if symbol in price_stream_service.prices:
                        await websocket.send_json(
                            {
                                "type": "price",
                                "symbol": symbol,
                                "price": str(price_stream_service.prices[symbol]),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
            except json.JSONDecodeError:
                logger.debug("Invalid JSON from client")
    except WebSocketDisconnect:
        price_stream_manager.disconnect(websocket)
    except Exception as exc:
        price_stream_manager.disconnect(websocket)
        logger.error("❌ WebSocket error: %s", exc)


@router.websocket("/ws/prices/{symbol}")
async def websocket_single_price(websocket: WebSocket, symbol: str):
    normalized = symbol.lower()
    await price_stream_manager.connect(websocket)

    try:
        while True:
            try:
                _ = await asyncio.wait_for(websocket.receive_text(), timeout=20)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "keep_alive", "timestamp": datetime.utcnow().isoformat()})

            if normalized in price_stream_service.prices:
                await websocket.send_json(
                    {
                        "type": "price",
                        "symbol": normalized,
                        "price": str(price_stream_service.prices[normalized]),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
    except WebSocketDisconnect:
        price_stream_manager.disconnect(websocket)
    except Exception as exc:
        price_stream_manager.disconnect(websocket)
        logger.error("❌ WebSocket error for %s: %s", symbol, exc)
