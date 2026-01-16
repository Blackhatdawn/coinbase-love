"""Real-time notification system with WebSocket support."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
import logging
import uuid
import json
import asyncio

from dependencies import get_current_user_id, get_db
from models import Notification, NotificationCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time notifications."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket for a user."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"✅ WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket for a user."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up empty user connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"❌ WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up failed connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)


# Global connection manager instance
manager = ConnectionManager()


# ============================================
# NOTIFICATION HELPERS
# ============================================

async def create_notification(
    db,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    link: Optional[str] = None,
    send_realtime: bool = True
) -> dict:
    """
    Create a notification and optionally send it in real-time via WebSocket.
    
    Types: info, success, warning, error, alert, price_alert, trade, deposit, withdrawal, transfer
    """
    notifications_collection = db.get_collection("notifications")
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        link=link
    )
    
    await notifications_collection.insert_one(notification.dict())
    
    # Send real-time notification via WebSocket
    if send_realtime:
        await manager.send_personal_message(
            {
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "notification_type": notification.type,
                    "link": notification.link,
                    "timestamp": notification.created_at.isoformat()
                }
            },
            user_id
        )
    
    logger.info(f"📬 Notification created for user {user_id}: {title}")
    
    return notification.dict()


# ============================================
# REST API ENDPOINTS
# ============================================

@router.get("")
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's notifications with pagination."""
    notifications_collection = db.get_collection("notifications")
    
    query = {"user_id": user_id}
    if unread_only:
        query["read"] = False
    
    notifications = await notifications_collection.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await notifications_collection.count_documents(query)
    unread_count = await notifications_collection.count_documents({"user_id": user_id, "read": False})
    
    return {
        "notifications": notifications,
        "total": total,
        "unread": unread_count,
        "skip": skip,
        "limit": limit
    }


@router.post("")
async def create_user_notification(
    data: NotificationCreate,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Create a notification for the current user (for testing or user-generated notes)."""
    notification = await create_notification(
        db, user_id, data.title, data.message, data.type, data.link
    )
    
    return {"message": "Notification created", "notification": notification}


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Mark a notification as read."""
    notifications_collection = db.get_collection("notifications")
    
    result = await notifications_collection.update_one(
        {"id": notification_id, "user_id": user_id},
        {"$set": {"read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Mark all notifications as read for the current user."""
    notifications_collection = db.get_collection("notifications")
    
    result = await notifications_collection.update_many(
        {"user_id": user_id, "read": False},
        {"$set": {"read": True}}
    )
    
    return {
        "message": "All notifications marked as read",
        "updated_count": result.modified_count
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Delete a notification."""
    notifications_collection = db.get_collection("notifications")
    
    result = await notifications_collection.delete_one({
        "id": notification_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted"}


# ============================================
# WEBSOCKET ENDPOINT
# ============================================

@router.websocket("/ws")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for real-time notifications.
    
    Connect with: ws://localhost:8000/api/notifications/ws?token=<access_token>
    
    Messages will be in format:
    {
        "type": "notification|price_alert|trade|system",
        "data": { ... }
    }
    """
    # Extract user_id from token (simplified - in production, verify JWT)
    # For now, we'll require token as query parameter
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    # TODO: Properly decode JWT token to get user_id
    # For now, using a simple approach (this should be improved with proper JWT verification)
    from auth import decode_token
    
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return
    
    await manager.connect(websocket, user_id)
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "system",
        "data": {
            "message": "Connected to notification stream",
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    
    try:
        while True:
            # Keep connection alive and listen for ping messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for keeping connection alive
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"Client {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


# ============================================
# NOTIFICATION TRIGGERS (Helper functions for other modules)
# ============================================

async def notify_deposit_completed(db, user_id: str, amount: float, currency: str):
    """Send notification when deposit is completed."""
    await create_notification(
        db, user_id,
        title="Deposit Completed",
        message=f"Your deposit of {amount} {currency} has been successfully processed.",
        notification_type="success",
        link="/dashboard"
    )


async def notify_withdrawal_processed(db, user_id: str, amount: float, currency: str, status: str):
    """Send notification when withdrawal status changes."""
    if status == "completed":
        await create_notification(
            db, user_id,
            title="Withdrawal Completed",
            message=f"Your withdrawal of {amount} {currency} has been completed.",
            notification_type="success",
            link="/transactions"
        )
    elif status == "processing":
        await create_notification(
            db, user_id,
            title="Withdrawal Processing",
            message=f"Your withdrawal of {amount} {currency} is being processed.",
            notification_type="info",
            link="/transactions"
        )


async def notify_trade_executed(db, user_id: str, side: str, amount: float, trading_pair: str, price: float):
    """Send notification when trade is executed."""
    await create_notification(
        db, user_id,
        title="Trade Executed",
        message=f"{side.upper()} order executed: {amount} {trading_pair} @ ${price}",
        notification_type="success",
        link="/trade"
    )


async def notify_price_alert(db, user_id: str, symbol: str, target_price: float, current_price: float):
    """Send notification when price alert is triggered."""
    await create_notification(
        db, user_id,
        title=f"Price Alert: {symbol}",
        message=f"{symbol} has reached ${current_price} (target: ${target_price})",
        notification_type="alert",
        link=f"/markets?symbol={symbol}"
    )


async def notify_transfer_received(db, user_id: str, amount: float, currency: str, sender_name: str):
    """Send notification when user receives a P2P transfer."""
    await create_notification(
        db, user_id,
        title="Transfer Received",
        message=f"You received {amount} {currency} from {sender_name}",
        notification_type="success",
        link="/transactions"
    )
