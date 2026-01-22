"""Shared helpers for transaction formatting and real-time updates."""

from datetime import datetime
from typing import Any, Dict, Optional
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

TRANSFER_TYPES = {"transfer_in", "transfer_out", "p2p_send", "p2p_receive"}
DISPLAY_TYPE_MAP = {
    "withdrawal": "withdraw",
    "transfer_in": "transfer",
    "transfer_out": "transfer",
    "p2p_send": "transfer",
    "p2p_receive": "transfer",
}


def normalize_type_filter(type_filter: Optional[str]) -> Optional[dict]:
    """Normalize UI-friendly type filters to database query filters."""
    if not type_filter:
        return None

    normalized = type_filter.lower()
    if normalized == "buy":
        return {"type": "trade", "amount": {"$gt": 0}}
    if normalized == "sell":
        return {"type": "trade", "amount": {"$lt": 0}}
    if normalized == "withdraw":
        return {"type": "withdrawal"}
    if normalized == "transfer":
        return {"type": {"$in": list(TRANSFER_TYPES)}}

    allowed = {"deposit", "withdrawal", "trade", "fee", "refund"}
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    return {"type": normalized}


def resolve_display_type(transaction: Dict[str, Any]) -> str:
    """Map internal transaction types to UI-friendly display types."""
    tx_type = transaction.get("type", "")
    if tx_type == "trade":
        return "buy" if transaction.get("amount", 0) >= 0 else "sell"
    return DISPLAY_TYPE_MAP.get(tx_type, tx_type)


def format_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Format transaction response with display-friendly fields."""
    created_at = transaction.get("created_at")
    if isinstance(created_at, datetime):
        created_at_value = created_at.isoformat()
    else:
        created_at_value = created_at

    display_type = resolve_display_type(transaction)
    return {
        "id": transaction.get("id"),
        "type": display_type,
        "rawType": transaction.get("type"),
        "amount": transaction.get("amount"),
        "currency": transaction.get("currency", "USD"),
        "symbol": transaction.get("symbol"),
        "status": transaction.get("status", "completed"),
        "description": transaction.get("description"),
        "reference": transaction.get("reference"),
        "createdAt": created_at_value,
    }


async def broadcast_transaction_event(
    user_id: str,
    transaction: Dict[str, Any],
    event: str = "transaction_update",
) -> None:
    """Broadcast a transaction update to a user's Socket.IO room."""
    try:
        from socketio_server import socketio_manager

        await socketio_manager.broadcast_to_user(
            user_id,
            event,
            {"transaction": format_transaction(transaction)},
        )
    except Exception as exc:
        logger.warning("Failed to broadcast transaction update: %s", exc)
