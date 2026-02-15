"""Earn endpoints for staking products and positions."""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dependencies import get_current_user_id, get_db
from config import settings

router = APIRouter(prefix="/earn", tags=["earn"])

PRODUCTS = [
    {"id": "btc-flex", "token": "BTC", "name": "Bitcoin Flexible", "type": "flexible", "apy": 5.2, "minAmount": 0.001, "lockPeriod": "Flexible", "tvl": 125000000, "icon": "₿", "color": "orange", "popular": True},
    {"id": "eth-30d", "token": "ETH", "name": "Ethereum 30-Day", "type": "locked", "apy": 8.5, "minAmount": 0.1, "lockPeriod": "30 days", "tvl": 89000000, "icon": "Ξ", "color": "violet", "popular": True, "lockDays": 30},
    {"id": "usdt-flex", "token": "USDT", "name": "USDT Savings", "type": "flexible", "apy": 12.0, "minAmount": 100, "lockPeriod": "Flexible", "tvl": 250000000, "icon": "$", "color": "emerald", "hot": True},
    {"id": "sol-60d", "token": "SOL", "name": "Solana 60-Day", "type": "locked", "apy": 15.2, "minAmount": 1, "lockPeriod": "60 days", "tvl": 45000000, "icon": "S", "color": "purple", "new": True, "lockDays": 60},
]


class CreateStakeRequest(BaseModel):
    product_id: str = Field(..., description="Earn product ID")
    amount: float = Field(..., gt=0, description="Stake amount in token units")


class CloseStakeRequest(BaseModel):
    stake_id: str = Field(..., description="Stake ID")


def _ensure_earn_enabled() -> None:
    if not settings.feature_staking_enabled:
        raise HTTPException(status_code=503, detail="Earn/staking is currently disabled")


def _find_product(product_id: str) -> Optional[dict]:
    return next((p for p in PRODUCTS if p["id"] == product_id), None)


def _calculate_rewards(stake: dict) -> float:
    created_at = stake.get("created_at") or datetime.utcnow()
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    elapsed_seconds = max((datetime.utcnow() - created_at).total_seconds(), 0)
    elapsed_days = elapsed_seconds / 86400
    apy = float(stake.get("apy", 0))
    principal = float(stake.get("amount", 0))

    return round(principal * (apy / 100) * (elapsed_days / 365), 8)


@router.get("/products")
async def get_earn_products():
    _ensure_earn_enabled()
    return {"products": PRODUCTS}


@router.get("/positions")
async def get_earn_positions(user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    _ensure_earn_enabled()
    stakes = db.get_collection("stakes")

    positions = await stakes.find({"user_id": user_id, "status": "active"}).sort("created_at", -1).to_list(100)
    normalized = []
    for position in positions:
        rewards = _calculate_rewards(position)
        normalized.append({
            "id": position.get("id") or str(position.get("_id")),
            "product": position.get("product", "Unknown product"),
            "token": position.get("token", "USD"),
            "amount": float(position.get("amount", 0)),
            "apy": float(position.get("apy", 0)),
            "rewards": rewards,
            "startDate": (position.get("created_at") or datetime.utcnow()).isoformat(),
            "lockPeriod": position.get("lock_period", "Flexible"),
            "daysRemaining": position.get("days_remaining"),
            "status": "active",
            "productId": position.get("product_id"),
        })

    return {"positions": normalized}


@router.post("/stake")
async def create_stake(payload: CreateStakeRequest, user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    _ensure_earn_enabled()

    product = _find_product(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Earn product not found")

    min_amount = float(product.get("minAmount", 0))
    if payload.amount < min_amount:
        raise HTTPException(status_code=400, detail=f"Minimum stake for this product is {min_amount} {product['token']}")

    token = str(product["token"]).upper()
    wallets = db.get_collection("wallets")
    wallet = await wallets.find_one({"user_id": user_id})
    balance = float((wallet or {}).get("balances", {}).get(token, 0))

    if balance < payload.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient {token} balance")

    days_remaining = product.get("lockDays") if product.get("type") == "locked" else None

    stake_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "product_id": product["id"],
        "product": product["name"],
        "token": token,
        "amount": payload.amount,
        "apy": product["apy"],
        "lock_period": product["lockPeriod"],
        "days_remaining": days_remaining,
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    stakes = db.get_collection("stakes")
    await stakes.insert_one(stake_doc)

    await wallets.update_one(
        {"user_id": user_id},
        {
            "$inc": {f"balances.{token}": -payload.amount},
            "$set": {"updated_at": datetime.utcnow()},
        },
        upsert=True,
    )

    transactions = db.get_collection("transactions")
    await transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "stake_create",
        "amount": payload.amount,
        "currency": token,
        "status": "completed",
        "reference": stake_doc["id"],
        "description": f"Staked into {product['name']}",
        "created_at": datetime.utcnow(),
    })

    return {"success": True, "stake": {**stake_doc, "rewards": 0.0, "startDate": stake_doc["created_at"].isoformat(), "lockPeriod": stake_doc["lock_period"]}}


@router.post("/redeem")
async def redeem_stake(payload: CloseStakeRequest, user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    _ensure_earn_enabled()

    stakes = db.get_collection("stakes")
    stake = await stakes.find_one({"id": payload.stake_id, "user_id": user_id, "status": "active"})
    if not stake:
        raise HTTPException(status_code=404, detail="Active stake not found")

    rewards = _calculate_rewards(stake)
    token = str(stake.get("token", "USD")).upper()
    principal = float(stake.get("amount", 0))
    total_credit = principal + rewards

    if stake.get("days_remaining"):
        created_at = stake.get("created_at") or datetime.utcnow()
        days_elapsed = (datetime.utcnow() - created_at).days
        if days_elapsed < int(stake["days_remaining"]):
            raise HTTPException(status_code=400, detail="This locked stake is not yet redeemable")

    await stakes.update_one(
        {"id": payload.stake_id},
        {
            "$set": {
                "status": "closed",
                "rewards_paid": rewards,
                "closed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        },
    )

    wallets = db.get_collection("wallets")
    await wallets.update_one(
        {"user_id": user_id},
        {
            "$inc": {f"balances.{token}": total_credit},
            "$set": {"updated_at": datetime.utcnow()},
        },
        upsert=True,
    )

    transactions = db.get_collection("transactions")
    await transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "stake_redeem",
        "amount": total_credit,
        "currency": token,
        "status": "completed",
        "reference": payload.stake_id,
        "description": f"Redeemed stake principal + rewards ({rewards} {token})",
        "created_at": datetime.utcnow(),
    })

    return {
        "success": True,
        "redeemed": {
            "stakeId": payload.stake_id,
            "principal": principal,
            "rewards": rewards,
            "total": total_credit,
            "token": token,
        },
    }
