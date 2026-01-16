"""
WebSocket Endpoints for Real-Time Price Streaming
Streams live cryptocurrency prices to connected clients
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Set, Dict, Optional
import asyncio
import json
import logging
from datetime import datetime

from services import price_stream_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


class PriceStreamManager:
    """Manages WebSocket connections and broadcasts price updates"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.last_broadcast: Dict[str, str] = {}
        self.broadcast_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        logger.info(f"📡 WebSocket connected (total: {len(self.active_connections)})")
        
        # Send initial status
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to price stream",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Unregister a disconnected WebSocket"""
        self.active_connections.discard(websocket)
        logger.info(f"📡 WebSocket disconnected (total: {len(self.active_connections)})")
    
    async def broadcast_price_update(self, prices: Dict[str, str]):
        """Broadcast price update to all connected clients"""
        if not self.active_connections:
            return
        
        message = {
            "type": "price_update",
            "prices": prices,
            "timestamp": datetime.now().isoformat(),
            "source": price_stream_service.current_source
        }
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_connection_status(self):
        """Broadcast connection status to all clients"""
        status = price_stream_service.get_status()
        
        message = {
            "type": "status",
            "state": status["state"],
            "source": status["source"],
            "is_running": status["is_running"],
            "prices_cached": status["prices_cached"],
            "last_update": status["last_update"],
            "timestamp": datetime.now().isoformat()
        }
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Error sending status to client: {e}")
    
    async def start_broadcast_loop(self):
        """Start continuous broadcasting of price updates"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("🔄 Starting WebSocket broadcast loop")
        
        while self.is_running:
            try:
                # Broadcast current prices every second
                if price_stream_service.prices and self.active_connections:
                    await self.broadcast_price_update(
                        {k: str(v) for k, v in price_stream_service.prices.items()}
                    )
                
                # Broadcast status every 10 seconds
                if len(self.active_connections) % 10 == 0:
                    await self.broadcast_connection_status()
                
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"❌ Error in broadcast loop: {e}")
                await asyncio.sleep(5)
    
    async def stop_broadcast_loop(self):
        """Stop the broadcast loop"""
        self.is_running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass


# Global manager instance
price_stream_manager = PriceStreamManager()


# ============================================
# WEBSOCKET ENDPOINTS
# ============================================

@router.websocket("/ws/prices")
async def websocket_price_stream(websocket: WebSocket):
    """
    Real-time cryptocurrency price stream WebSocket.
    
    Connection URL: wss://cryptovault-api.onrender.com/ws/prices
    
    Message Types:
    1. connection: Sent when client first connects
    2. price_update: Sent whenever prices change (1-20/sec)
    3. status: Connection status updates (every 10s)
    
    Example Messages:
    {
        "type": "price_update",
        "prices": {
            "bitcoin": "45000.50",
            "ethereum": "2500.25"
        },
        "timestamp": "2026-01-16T05:00:00.000Z",
        "source": "coincap"
    }
    
    {
        "type": "status",
        "state": "connected",
        "source": "coincap",
        "prices_cached": 1247,
        "timestamp": "2026-01-16T05:00:00.000Z"
    }
    """
    await price_stream_manager.connect(websocket)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive any messages from client (mainly for keep-alive)
            data = await websocket.receive_text()
            
            # Handle client messages
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping to keep connection alive
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif message_type == "get_status":
                    # Send current status on demand
                    status = price_stream_service.get_status()
                    await websocket.send_json({
                        "type": "status",
                        "state": status["state"],
                        "source": status["source"],
                        "prices_cached": status["prices_cached"],
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif message_type == "get_price":
                    # Send specific price on demand
                    symbol = message.get("symbol")
                    if symbol and symbol in price_stream_service.prices:
                        await websocket.send_json({
                            "type": "price",
                            "symbol": symbol,
                            "price": str(price_stream_service.prices[symbol]),
                            "timestamp": datetime.now().isoformat()
                        })
            
            except json.JSONDecodeError:
                logger.debug("Invalid JSON from client")
            except Exception as e:
                logger.warning(f"⚠️ Error handling client message: {e}")
    
    except WebSocketDisconnect:
        price_stream_manager.disconnect(websocket)
        logger.info("🔌 WebSocket disconnected (client closed)")
    
    except Exception as e:
        price_stream_manager.disconnect(websocket)
        logger.error(f"❌ WebSocket error: {e}")


@router.websocket("/ws/prices/{symbol}")
async def websocket_single_price(websocket: WebSocket, symbol: str):
    """
    Real-time price stream for a specific cryptocurrency.
    
    Connection URL: wss://cryptovault-api.onrender.com/ws/prices/bitcoin
    
    Only receives updates for the specified symbol, reducing bandwidth.
    """
    await price_stream_manager.connect(websocket)
    
    try:
        while True:
            # Check for incoming messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            
            except asyncio.TimeoutError:
                # Send keep-alive ping if no message received
                await websocket.send_json({"type": "keep_alive"})
            except json.JSONDecodeError:
                pass
            
            # Send price update if symbol exists
            if symbol in price_stream_service.prices:
                price = price_stream_service.prices[symbol]
                await websocket.send_json({
                    "type": "price",
                    "symbol": symbol,
                    "price": str(price),
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        price_stream_manager.disconnect(websocket)
    except Exception as e:
        price_stream_manager.disconnect(websocket)
        logger.error(f"❌ WebSocket error for {symbol}: {e}")
