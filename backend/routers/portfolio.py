"""Portfolio management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List

from ..models import Portfolio, Holding, HoldingCreate
from ..dependencies import get_current_user_id, get_db
from ..coingecko_service import coingecko_service

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("")
async def get_portfolio(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get user's complete portfolio with real-time prices."""
    portfolios_collection = db.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})

    if not portfolio_doc:
        portfolio = Portfolio(user_id=user_id)
        await portfolios_collection.insert_one(portfolio.dict())
        return {"portfolio": {"totalBalance": 0, "holdings": []}}

    holdings = portfolio_doc.get("holdings", [])
    prices = await coingecko_service.get_prices()

    total_balance = 0
    updated_holdings = []

    for holding in holdings:
        crypto = next((c for c in prices if c["symbol"].upper() == holding["symbol"].upper()), None)
        if crypto and "current_price" in crypto:
            current_price = crypto["current_price"]
            current_value = holding["amount"] * current_price
            total_balance += current_value
            updated_holdings.append({
                "symbol": holding["symbol"],
                "name": crypto.get("name", holding.get("name")),
                "amount": holding["amount"],
                "current_price": current_price,
                "value": round(current_value, 2),
                "allocation": 0
            })
        else:
            updated_holdings.append({
                **holding,
                "current_price": 0,
                "value": 0,
                "allocation": 0
            })

    for h in updated_holdings:
        h["allocation"] = round((h["value"] / total_balance * 100), 2) if total_balance > 0 else 0

    return {
        "portfolio": {
            "totalBalance": round(total_balance, 2),
            "holdings": updated_holdings
        }
    }


@router.get("/holding/{symbol}")
async def get_holding(
    symbol: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get specific holding by symbol."""
    portfolios_collection = db.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holdings = portfolio_doc.get("holdings", [])
    holding = next((h for h in holdings if h["symbol"] == symbol.upper()), None)

    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    return {"holding": holding}


@router.post("/holding")
async def add_holding(
    holding_data: HoldingCreate,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Add or update holding in portfolio."""
    portfolios_collection = db.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})

    if not portfolio_doc:
        portfolio = Portfolio(user_id=user_id)
        await portfolios_collection.insert_one(portfolio.dict())
        holdings = []
    else:
        holdings = portfolio_doc.get("holdings", [])

    prices = await coingecko_service.get_prices()
    crypto = next((c for c in prices if c["symbol"].upper() == holding_data.symbol.upper()), None)
    if not crypto:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")

    new_holding = {
        "symbol": holding_data.symbol.upper(),
        "name": holding_data.name,
        "amount": holding_data.amount,
        "value": holding_data.amount * crypto["current_price"],
        "allocation": 0
    }

    existing_idx = next((i for i, h in enumerate(holdings) if h["symbol"] == holding_data.symbol.upper()), None)

    if existing_idx is not None:
        holdings[existing_idx]["amount"] += holding_data.amount
        holdings[existing_idx]["value"] = holdings[existing_idx]["amount"] * crypto["current_price"]
    else:
        holdings.append(new_holding)

    await portfolios_collection.update_one(
        {"user_id": user_id},
        {"$set": {"holdings": holdings, "updated_at": datetime.utcnow()}}
    )

    return {"message": "Holding added successfully", "holding": new_holding}


@router.delete("/holding/{symbol}")
async def delete_holding(
    symbol: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Delete holding from portfolio."""
    portfolios_collection = db.get_collection("portfolios")
    portfolio_doc = await portfolios_collection.find_one({"user_id": user_id})
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holdings = portfolio_doc.get("holdings", [])
    holdings = [h for h in holdings if h["symbol"] != symbol.upper()]

    await portfolios_collection.update_one(
        {"user_id": user_id},
        {"$set": {"holdings": holdings, "updated_at": datetime.utcnow()}}
    )

    return {"message": "Holding deleted successfully"}
