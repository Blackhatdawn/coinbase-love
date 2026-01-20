"""Transaction history endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import logging

from dependencies import get_current_user_id, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["transactions"])

# ============================================
# TRANSACTION TYPE NORMALIZATION
# ============================================

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


def resolve_display_type(transaction: dict) -> str:
    """Map internal transaction types to UI-friendly display types."""
    tx_type = transaction.get("type", "")
    if tx_type == "trade":
        return "buy" if transaction.get("amount", 0) >= 0 else "sell"
    return DISPLAY_TYPE_MAP.get(tx_type, tx_type)


def format_transaction(transaction: dict) -> dict:
    """Format transaction response with display-friendly fields."""
    display_type = resolve_display_type(transaction)
    return {
        "id": transaction["id"],
        "type": display_type,
        "rawType": transaction.get("type"),
        "amount": transaction["amount"],
        "currency": transaction.get("currency", "USD"),
        "symbol": transaction.get("symbol"),
        "status": transaction.get("status", "completed"),
        "description": transaction.get("description"),
        "reference": transaction.get("reference"),
        "createdAt": transaction["created_at"].isoformat()
    }


@router.get("")
async def get_transactions(
    skip: int = 0,
    limit: int = 50,
    type: Optional[str] = None,  # deposit, withdrawal, trade, fee
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's transaction history."""
    transactions_collection = db.get_collection("transactions")
    
    # Build query
    query = {"user_id": user_id}
    type_filter = normalize_type_filter(type)
    if type_filter:
        query.update(type_filter)
    
    # Get transactions
    transactions = await transactions_collection.find(
        query
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await transactions_collection.count_documents(query)
    
    return {
        "transactions": [format_transaction(tx) for tx in transactions],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get a specific transaction."""
    transactions_collection = db.get_collection("transactions")
    
    transaction = await transactions_collection.find_one({
        "id": transaction_id,
        "user_id": user_id
    })
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "transaction": format_transaction(transaction)
    }


@router.get("/summary/stats")
async def get_transaction_stats(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get transaction statistics summary."""
    transactions_collection = db.get_collection("transactions")
    
    # Aggregate by type
    pipeline = [
        {"$match": {"user_id": user_id, "status": "completed"}},
        {
            "$group": {
                "_id": "$type",
                "total_amount": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        }
    ]
    
    results = await transactions_collection.aggregate(pipeline).to_list(10)
    
    stats = {}
    for result in results:
        tx_type = result["_id"]
        stats[tx_type] = {
            "totalAmount": result["total_amount"],
            "count": result["count"]
        }
    
    return {
        "stats": stats,
        "totalDeposits": stats.get("deposit", {}).get("totalAmount", 0),
        "totalWithdrawals": stats.get("withdrawal", {}).get("totalAmount", 0),
        "totalTrades": stats.get("trade", {}).get("count", 0)
    }
