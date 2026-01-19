"""Transaction history endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import logging

from dependencies import get_current_user_id, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["transactions"])


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
    if type:
        if type not in ["deposit", "withdrawal", "trade", "fee"]:
            raise HTTPException(status_code=400, detail="Invalid transaction type")
        query["type"] = type
    
    # Get transactions
    transactions = await transactions_collection.find(
        query
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await transactions_collection.count_documents(query)
    
    return {
        "transactions": [
            {
                "id": tx["id"],
                "type": tx["type"],
                "amount": tx["amount"],
                "currency": tx.get("currency", "USD"),
                "symbol": tx.get("symbol"),
                "status": tx.get("status", "completed"),
                "description": tx.get("description"),
                "reference": tx.get("reference"),
                "createdAt": tx["created_at"].isoformat()
            }
            for tx in transactions
        ],
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
        "transaction": {
            "id": transaction["id"],
            "type": transaction["type"],
            "amount": transaction["amount"],
            "currency": transaction.get("currency", "USD"),
            "symbol": transaction.get("symbol"),
            "status": transaction.get("status", "completed"),
            "description": transaction.get("description"),
            "reference": transaction.get("reference"),
            "createdAt": transaction["created_at"].isoformat()
        }
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
