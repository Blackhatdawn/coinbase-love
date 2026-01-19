"""
API v1 Router - Versioned API endpoints
"""

from fastapi import APIRouter
from . import auth, crypto, portfolio, trading, transactions, users, wallet, alerts, notifications, prices, transfers

# Create main v1 router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include all v1 routers
api_v1_router.include_router(auth.router)
api_v1_router.include_router(crypto.router)
api_v1_router.include_router(portfolio.router)
api_v1_router.include_router(trading.router)
api_v1_router.include_router(transactions.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(wallet.router)
api_v1_router.include_router(alerts.router)
api_v1_router.include_router(notifications.router)
api_v1_router.include_router(prices.router)
api_v1_router.include_router(transfers.router)