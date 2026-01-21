"""
Enterprise WebSocket Endpoints v2
Production-ready WebSocket endpoints with enhanced security and monitoring.

Features:
- Connection limits and rate limiting
- Health monitoring endpoint
- Metrics collection
- Graceful error handling
- Message validation
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from typing import Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime

from services import price_stream_service
from services.websocket_manager import enterprise_ws_manager, ConnectionState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2", tags=["websocket-v2"])


# ============================================
# PRICE STREAMING ENDPOINTS
# ============================================

@router.websocket("/ws/prices")
async def websocket_price_stream_v2(websocket: WebSocket):
    """
    Real-time cryptocurrency price stream WebSocket (Enterprise Edition).
    
    Connection URL: wss://<api-host>/api/v2/ws/prices
    
    Features:
    - Connection limits per IP (prevents DoS)
    - Message rate limiting
    - Automatic reconnection support
    - Health monitoring
    
    Message Types Received:
    - connection: Initial connection confirmation
    - price_update: Real-time price updates (1-20/sec)
    - status: Service status updates
    - pong: Response to ping
    - error: Error messages
    
    Client Commands:
    - {"type": "ping"} - Keep connection alive
    - {"type": "get_status"} - Request service status
    - {"type": "get_price", "symbol": "bitcoin"} - Get specific price
    - {"type": "subscribe", "channels": ["bitcoin", "ethereum"]} - Subscribe to specific coins
    
    Example Price Update:
    {
        "type": "price_update",
        "prices": {"bitcoin": "45000.50", "ethereum": "2500.25"},
        "timestamp": "2026-01-21T10:00:00.000Z",
        "source": "coincap"
    }
    """
    # Accept connection with enterprise security checks
    accepted = await enterprise_ws_manager.accept_connection(websocket)
    if not accepted:
        return
    
    # Subscribe to price channel
    enterprise_ws_manager.subscribe(websocket, "prices")
    
    # Start broadcast task for this connection
    broadcast_task = asyncio.create_task(_price_broadcast_loop(websocket))
    
    try:
        while True:
            # Receive and process client messages
            message = await enterprise_ws_manager.receive_json(websocket, timeout=60)
            
            if message is None:
                # Timeout - send keep-alive
                await enterprise_ws_manager.send_json(websocket, {
                    "type": "keep_alive",
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue
            
            # Handle client commands
            await _handle_price_client_message(websocket, message)
    
    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected from price stream")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass
        enterprise_ws_manager.disconnect(websocket)


async def _price_broadcast_loop(websocket: WebSocket):
    """Background task to broadcast price updates to a connection."""
    last_prices = {}
    
    while True:
        try:
            await asyncio.sleep(1)
            
            # Get current prices
            current_prices = price_stream_service.get_all_prices()
            if not current_prices:
                continue
            
            # Only send if prices have changed
            if current_prices != last_prices:
                await enterprise_ws_manager.send_json(websocket, {
                    "type": "price_update",
                    "prices": {k: str(v) for k, v in current_prices.items()},
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": price_stream_service.current_source if hasattr(price_stream_service, 'current_source') else "coincap"
                })
                last_prices = current_prices.copy()
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Broadcast error: {e}")
            await asyncio.sleep(5)


async def _handle_price_client_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle client message on price stream."""
    message_type = message.get("type")
    
    if message_type == "ping":
        await enterprise_ws_manager.send_json(websocket, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "get_status":
        status = price_stream_service.get_status()
        await enterprise_ws_manager.send_json(websocket, {
            "type": "status",
            **status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "get_price":
        symbol = message.get("symbol", "").lower()
        if symbol:
            price = await price_stream_service.get_price(symbol)
            if price is not None:
                await enterprise_ws_manager.send_json(websocket, {
                    "type": "price",
                    "symbol": symbol,
                    "price": str(price),
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                await enterprise_ws_manager.send_json(websocket, {
                    "type": "error",
                    "code": "SYMBOL_NOT_FOUND",
                    "message": f"Price not available for {symbol}"
                })
    
    elif message_type == "subscribe":
        channels = message.get("channels", [])
        for channel in channels:
            enterprise_ws_manager.subscribe(websocket, f"coin:{channel}")
        await enterprise_ws_manager.send_json(websocket, {
            "type": "subscribed",
            "channels": channels
        })
    
    elif message_type == "unsubscribe":
        channels = message.get("channels", [])
        for channel in channels:
            enterprise_ws_manager.unsubscribe(websocket, f"coin:{channel}")
        await enterprise_ws_manager.send_json(websocket, {
            "type": "unsubscribed",
            "channels": channels
        })


@router.websocket("/ws/prices/{symbol}")
async def websocket_single_price_v2(websocket: WebSocket, symbol: str):
    """
    Real-time price stream for a specific cryptocurrency (Enterprise Edition).
    
    Connection URL: wss://<api-host>/api/v2/ws/prices/bitcoin
    
    Only receives updates for the specified symbol, reducing bandwidth.
    """
    symbol = symbol.lower()
    
    # Accept connection
    accepted = await enterprise_ws_manager.accept_connection(websocket)
    if not accepted:
        return
    
    # Subscribe to specific coin channel
    enterprise_ws_manager.subscribe(websocket, f"coin:{symbol}")
    
    try:
        last_price = None
        
        while True:
            # Check for incoming messages with timeout
            try:
                message = await enterprise_ws_manager.receive_json(websocket, timeout=30)
                
                if message:
                    if message.get("type") == "ping":
                        await enterprise_ws_manager.send_json(websocket, {"type": "pong"})
                else:
                    # Timeout - send keep-alive
                    await enterprise_ws_manager.send_json(websocket, {"type": "keep_alive"})
            
            except asyncio.TimeoutError:
                pass
            
            # Get and send price if changed
            price = await price_stream_service.get_price(symbol)
            if price is not None and price != last_price:
                await enterprise_ws_manager.send_json(websocket, {
                    "type": "price",
                    "symbol": symbol,
                    "price": str(price),
                    "timestamp": datetime.utcnow().isoformat()
                })
                last_price = price
            
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ WebSocket error for {symbol}: {e}")
    finally:
        enterprise_ws_manager.disconnect(websocket)


# ============================================
# HEALTH & MONITORING ENDPOINTS
# ============================================

@router.get("/ws/health")
async def websocket_health():
    """
    WebSocket system health and metrics endpoint.
    
    Returns comprehensive information about:
    - Active connections and their states
    - Message throughput
    - Channel subscriptions
    - System limits and configuration
    """
    metrics = enterprise_ws_manager.get_metrics()
    price_status = price_stream_service.get_status()
    
    return {
        "status": "healthy" if not metrics["is_shutting_down"] else "shutting_down",
        "websocket_manager": metrics,
        "price_stream": price_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ws/connections")
async def list_connections():
    """
    List active WebSocket connections (for admin/debugging).
    
    Note: In production, this should be protected by admin authentication.
    """
    metrics = enterprise_ws_manager.get_metrics()
    
    return {
        "total_connections": metrics["connections"]["current"],
        "connections_by_state": metrics["connections"]["by_state"],
        "unique_ips": metrics["connections"]["unique_ips"],
        "authenticated_users": metrics["connections"]["unique_users"],
        "channel_subscriptions": metrics["channels"],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ws/metrics")
async def websocket_metrics():
    """
    Prometheus-compatible metrics endpoint for WebSocket monitoring.
    
    Returns metrics in text format for Prometheus scraping.
    """
    metrics = enterprise_ws_manager.get_metrics()
    
    # Format as Prometheus metrics
    lines = [
        "# HELP websocket_connections_total Total active WebSocket connections",
        "# TYPE websocket_connections_total gauge",
        f"websocket_connections_total {metrics['connections']['current']}",
        "",
        "# HELP websocket_connections_ever Total connections since startup",
        "# TYPE websocket_connections_ever counter",
        f"websocket_connections_ever {metrics['connections']['total_ever']}",
        "",
        "# HELP websocket_messages_sent_total Total messages sent",
        "# TYPE websocket_messages_sent_total counter",
        f"websocket_messages_sent_total {metrics['messages']['sent']}",
        "",
        "# HELP websocket_messages_received_total Total messages received",
        "# TYPE websocket_messages_received_total counter",
        f"websocket_messages_received_total {metrics['messages']['received']}",
        "",
        "# HELP websocket_bytes_sent_total Total bytes sent",
        "# TYPE websocket_bytes_sent_total counter",
        f"websocket_bytes_sent_total {metrics['messages']['bytes_sent']}",
        "",
        "# HELP websocket_unique_ips Unique IP addresses connected",
        "# TYPE websocket_unique_ips gauge",
        f"websocket_unique_ips {metrics['connections']['unique_ips']}",
        "",
        "# HELP websocket_authenticated_users Authenticated users connected",
        "# TYPE websocket_authenticated_users gauge",
        f"websocket_authenticated_users {metrics['connections']['unique_users']}",
        "",
        "# HELP websocket_uptime_seconds WebSocket manager uptime",
        "# TYPE websocket_uptime_seconds gauge",
        f"websocket_uptime_seconds {metrics['uptime_seconds']:.2f}",
    ]
    
    # Add channel subscriptions
    lines.append("")
    lines.append("# HELP websocket_channel_subscribers Subscribers per channel")
    lines.append("# TYPE websocket_channel_subscribers gauge")
    for channel, count in metrics["channels"].items():
        safe_channel = channel.replace('"', '\\"')
        lines.append(f'websocket_channel_subscribers{{channel="{safe_channel}"}} {count}')
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines), media_type="text/plain")


# ============================================
# ADMIN ENDPOINTS
# ============================================

@router.post("/ws/broadcast")
async def admin_broadcast(
    message: Dict[str, Any],
    channel: Optional[str] = None,
    authenticated_only: bool = False
):
    """
    Broadcast a message to WebSocket clients (admin only).
    
    Note: In production, this should be protected by admin authentication.
    """
    if channel:
        sent_count = await enterprise_ws_manager.broadcast_to_channel(channel, message)
    else:
        sent_count = await enterprise_ws_manager.broadcast_all(
            message,
            only_authenticated=authenticated_only
        )
    
    return {
        "success": True,
        "sent_to": sent_count,
        "channel": channel,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/ws/shutdown")
async def initiate_graceful_shutdown(drain_timeout: int = 10):
    """
    Initiate graceful WebSocket shutdown (admin only).
    
    Note: In production, this should be protected by admin authentication.
    """
    asyncio.create_task(enterprise_ws_manager.graceful_shutdown(drain_timeout))
    
    return {
        "message": "Graceful shutdown initiated",
        "drain_timeout": drain_timeout,
        "timestamp": datetime.utcnow().isoformat()
    }
