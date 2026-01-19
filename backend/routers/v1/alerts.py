"""Price alerts management endpoints."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uuid
import logging

from dependencies import get_current_user_id, get_db, get_limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class AlertCreate(BaseModel):
    symbol: str
    targetPrice: float
    condition: str  # 'above' or 'below'
    notifyPush: bool = True
    notifyEmail: bool = True


class AlertUpdate(BaseModel):
    isActive: Optional[bool] = None
    targetPrice: Optional[float] = None
    condition: Optional[str] = None
    notifyPush: Optional[bool] = None
    notifyEmail: Optional[bool] = None


# ============================================
# HELPER FUNCTIONS
# ============================================

async def log_audit(db, user_id: str, action: str, resource: Optional[str] = None,
                    ip_address: Optional[str] = None, details: Optional[dict] = None):
    """Log audit event."""
    from models import AuditLog
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        details=details
    )
    await db.get_collection("audit_logs").insert_one(audit_log.dict())


# ============================================
# CRUD ENDPOINTS
# ============================================

@router.get("")
async def get_alerts(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get all price alerts for the current user."""
    alerts_collection = db.get_collection("price_alerts")
    
    alerts = await alerts_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "alerts": [
            {
                "id": alert["id"],
                "symbol": alert["symbol"],
                "targetPrice": alert["target_price"],
                "condition": alert["condition"],
                "isActive": alert.get("is_active", True),
                "notifyPush": alert.get("notify_push", True),
                "notifyEmail": alert.get("notify_email", True),
                "createdAt": alert["created_at"].isoformat(),
                "triggeredAt": alert.get("triggered_at").isoformat() if alert.get("triggered_at") else None
            }
            for alert in alerts
        ]
    }


@router.post("")
async def create_alert(
    data: AlertCreate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Create a new price alert."""
    
    
    # Validate condition
    if data.condition not in ["above", "below"]:
        raise HTTPException(status_code=400, detail="Condition must be 'above' or 'below'")
    
    # Validate target price
    if data.targetPrice <= 0:
        raise HTTPException(status_code=400, detail="Target price must be positive")
    
    # Validate symbol (basic check)
    valid_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LTC", "LINK"]
    if data.symbol.upper() not in valid_symbols:
        raise HTTPException(status_code=400, detail=f"Invalid symbol. Supported: {', '.join(valid_symbols)}")
    
    # Check alert limit (max 20 active alerts per user)
    alerts_collection = db.get_collection("price_alerts")
    active_count = await alerts_collection.count_documents({
        "user_id": user_id,
        "is_active": True
    })
    
    if active_count >= 20:
        raise HTTPException(status_code=400, detail="Maximum 20 active alerts allowed")
    
    # Create alert
    alert_id = str(uuid.uuid4())
    alert_doc = {
        "id": alert_id,
        "user_id": user_id,
        "symbol": data.symbol.upper(),
        "target_price": data.targetPrice,
        "condition": data.condition,
        "is_active": True,
        "notify_push": data.notifyPush,
        "notify_email": data.notifyEmail,
        "created_at": datetime.utcnow(),
        "triggered_at": None,
        "updated_at": datetime.utcnow()
    }
    
    await alerts_collection.insert_one(alert_doc)
    
    # Log audit
    await log_audit(
        db, user_id, "ALERT_CREATED",
        resource=alert_id,
        ip_address=request.client.host,
        details={"symbol": data.symbol, "target_price": data.targetPrice, "condition": data.condition}
    )
    
    logger.info(f"✅ Alert created: {data.symbol} {data.condition} ${data.targetPrice}")
    
    return {
        "message": "Alert created successfully",
        "alert": {
            "id": alert_id,
            "symbol": data.symbol.upper(),
            "targetPrice": data.targetPrice,
            "condition": data.condition,
            "isActive": True,
            "notifyPush": data.notifyPush,
            "notifyEmail": data.notifyEmail,
            "createdAt": alert_doc["created_at"].isoformat(),
            "triggeredAt": None
        }
    }


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get a specific price alert."""
    alerts_collection = db.get_collection("price_alerts")
    
    alert = await alerts_collection.find_one({
        "id": alert_id,
        "user_id": user_id
    })
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "alert": {
            "id": alert["id"],
            "symbol": alert["symbol"],
            "targetPrice": alert["target_price"],
            "condition": alert["condition"],
            "isActive": alert.get("is_active", True),
            "notifyPush": alert.get("notify_push", True),
            "notifyEmail": alert.get("notify_email", True),
            "createdAt": alert["created_at"].isoformat(),
            "triggeredAt": alert.get("triggered_at").isoformat() if alert.get("triggered_at") else None
        }
    }


@router.patch("/{alert_id}")
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Update a price alert."""
    alerts_collection = db.get_collection("price_alerts")
    
    # Find existing alert
    alert = await alerts_collection.find_one({
        "id": alert_id,
        "user_id": user_id
    })
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    
    if data.isActive is not None:
        update_doc["is_active"] = data.isActive
    if data.targetPrice is not None:
        if data.targetPrice <= 0:
            raise HTTPException(status_code=400, detail="Target price must be positive")
        update_doc["target_price"] = data.targetPrice
    if data.condition is not None:
        if data.condition not in ["above", "below"]:
            raise HTTPException(status_code=400, detail="Condition must be 'above' or 'below'")
        update_doc["condition"] = data.condition
    if data.notifyPush is not None:
        update_doc["notify_push"] = data.notifyPush
    if data.notifyEmail is not None:
        update_doc["notify_email"] = data.notifyEmail
    
    await alerts_collection.update_one(
        {"id": alert_id},
        {"$set": update_doc}
    )
    
    # Get updated alert
    updated_alert = await alerts_collection.find_one({"id": alert_id})
    
    logger.info(f"✅ Alert updated: {alert_id}")
    
    return {
        "message": "Alert updated successfully",
        "alert": {
            "id": updated_alert["id"],
            "symbol": updated_alert["symbol"],
            "targetPrice": updated_alert["target_price"],
            "condition": updated_alert["condition"],
            "isActive": updated_alert.get("is_active", True),
            "notifyPush": updated_alert.get("notify_push", True),
            "notifyEmail": updated_alert.get("notify_email", True),
            "createdAt": updated_alert["created_at"].isoformat(),
            "triggeredAt": updated_alert.get("triggered_at").isoformat() if updated_alert.get("triggered_at") else None
        }
    }


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Delete a price alert."""
    alerts_collection = db.get_collection("price_alerts")
    
    # Find existing alert
    alert = await alerts_collection.find_one({
        "id": alert_id,
        "user_id": user_id
    })
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await alerts_collection.delete_one({"id": alert_id})
    
    # Log audit
    await log_audit(
        db, user_id, "ALERT_DELETED",
        resource=alert_id,
        ip_address=request.client.host
    )
    
    logger.info(f"✅ Alert deleted: {alert_id}")
    
    return {"message": "Alert deleted successfully"}


# ============================================
# ALERT TRIGGERING (called by price service)
# ============================================

async def check_and_trigger_alerts(db, symbol: str, current_price: float):
    """
    Check if any alerts should be triggered based on current price.
    This function is called by the price feed service.
    """
    alerts_collection = db.get_collection("price_alerts")
    
    # Find all active alerts for this symbol
    alerts = await alerts_collection.find({
        "symbol": symbol.upper(),
        "is_active": True,
        "triggered_at": None
    }).to_list(1000)
    
    triggered = []
    
    for alert in alerts:
        should_trigger = False
        
        if alert["condition"] == "above" and current_price >= alert["target_price"]:
            should_trigger = True
        elif alert["condition"] == "below" and current_price <= alert["target_price"]:
            should_trigger = True
        
        if should_trigger:
            # Mark as triggered
            await alerts_collection.update_one(
                {"id": alert["id"]},
                {
                    "$set": {
                        "triggered_at": datetime.utcnow(),
                        "is_active": False,
                        "triggered_price": current_price
                    }
                }
            )
            
            triggered.append({
                "alert_id": alert["id"],
                "user_id": alert["user_id"],
                "symbol": alert["symbol"],
                "target_price": alert["target_price"],
                "condition": alert["condition"],
                "current_price": current_price,
                "notify_push": alert.get("notify_push", True),
                "notify_email": alert.get("notify_email", True)
            })
            
            logger.info(f"🔔 Alert triggered: {alert['symbol']} {alert['condition']} ${alert['target_price']} (now: ${current_price})")
    
    return triggered
