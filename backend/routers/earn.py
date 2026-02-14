"""Earn endpoints for staking products and positions."""

from fastapi import APIRouter, Depends

from dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/earn", tags=["earn"])

PRODUCTS = [
    {"id": "btc-flex", "token": "BTC", "name": "Bitcoin Flexible", "type": "flexible", "apy": 5.2, "minAmount": 0.001, "lockPeriod": "Flexible", "tvl": 125000000, "icon": "₿", "color": "orange", "popular": True},
    {"id": "eth-30d", "token": "ETH", "name": "Ethereum 30-Day", "type": "locked", "apy": 8.5, "minAmount": 0.1, "lockPeriod": "30 days", "tvl": 89000000, "icon": "Ξ", "color": "violet", "popular": True},
    {"id": "usdt-flex", "token": "USDT", "name": "USDT Savings", "type": "flexible", "apy": 12.0, "minAmount": 100, "lockPeriod": "Flexible", "tvl": 250000000, "icon": "$", "color": "emerald", "hot": True},
]


@router.get("/products")
async def get_earn_products():
    return {"products": PRODUCTS}


@router.get("/positions")
async def get_earn_positions(user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    stakes = db.get_collection("stakes")
    positions = await stakes.find({"user_id": user_id, "status": "active"}).sort("created_at", -1).to_list(100)
    return {"positions": positions}
