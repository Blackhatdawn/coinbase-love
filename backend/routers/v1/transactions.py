"""Transaction history endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
import logging
import csv
from io import StringIO

from dependencies import get_current_user_id, get_db
from services.transactions_utils import format_transaction, normalize_type_filter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["transactions"])

MAX_EXPORT_LIMIT = 5000


class TransactionExportRequest(BaseModel):
    """Export transactions to CSV or JSON."""

    format: Literal["csv", "json"] = "csv"
    type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=MAX_EXPORT_LIMIT, ge=1, le=MAX_EXPORT_LIMIT)


async def log_audit(
    db,
    user_id: str,
    action: str,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Log audit event."""
    from models import AuditLog

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        details=details,
    )
    await db.get_collection("audit_logs").insert_one(audit_log.dict())


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


@router.post("/export")
async def export_transactions(
    payload: TransactionExportRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Export transactions in CSV or JSON format."""
    if payload.start_date and payload.end_date and payload.start_date > payload.end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    transactions_collection = db.get_collection("transactions")

    query = {"user_id": user_id}
    type_filter = normalize_type_filter(payload.type)
    if type_filter:
        query.update(type_filter)

    if payload.start_date or payload.end_date:
        date_filter = {}
        if payload.start_date:
            date_filter["$gte"] = payload.start_date
        if payload.end_date:
            date_filter["$lte"] = payload.end_date
        query["created_at"] = date_filter

    limit = min(payload.limit, MAX_EXPORT_LIMIT)
    transactions = await transactions_collection.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    formatted = [format_transaction(tx) for tx in transactions]

    await log_audit(
        db,
        user_id,
        "TRANSACTIONS_EXPORTED",
        ip_address=request.client.host if request.client else None,
        details={
            "format": payload.format,
            "count": len(formatted),
            "type": payload.type,
        }
    )

    if payload.format == "json":
        return {"transactions": formatted, "count": len(formatted)}

    output = StringIO()
    fieldnames = [
        "id",
        "type",
        "rawType",
        "amount",
        "currency",
        "symbol",
        "status",
        "description",
        "reference",
        "createdAt",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(formatted)

    filename = f"transactions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


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
