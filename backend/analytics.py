"""
Business Analytics and Performance Monitoring for CryptoVault.

Provides:
- Trading volume analytics
- User activity tracking
- Revenue metrics
- Conversion funnel analysis
- Performance monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class BusinessAnalytics:
    """Business metrics and analytics engine."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # ============================================
    # USER ANALYTICS
    # ============================================
    
    async def get_user_growth(self, days: int = 30) -> dict:
        """Get user registration growth over time."""
        start_date = datetime.utcnow() - timedelta(days=days)
        users_collection = self.db.get_collection("users")
        
        # Total users
        total_users = await users_collection.count_documents({})
        
        # New users in period
        new_users = await users_collection.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Verified users
        verified_users = await users_collection.count_documents({
            "email_verified": True
        })
        
        # Active users (logged in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = await users_collection.count_documents({
            "last_login": {"$gte": week_ago}
        })
        
        # Daily breakdown
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_signups = await users_collection.aggregate(pipeline).to_list(days)
        
        return {
            "total_users": total_users,
            "new_users_period": new_users,
            "verified_users": verified_users,
            "verified_rate": f"{(verified_users / total_users * 100) if total_users > 0 else 0:.2f}%",
            "active_users_7d": active_users,
            "activity_rate": f"{(active_users / total_users * 100) if total_users > 0 else 0:.2f}%",
            "daily_signups": daily_signups
        }
    
    async def get_user_retention(self, cohort_days: int = 30) -> dict:
        """Calculate user retention metrics."""
        users_collection = self.db.get_collection("users")
        
        # Users created in cohort period
        cohort_start = datetime.utcnow() - timedelta(days=cohort_days)
        cohort_users = await users_collection.count_documents({
            "created_at": {"$gte": cohort_start}
        })
        
        # Users from cohort who logged in within last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        retained_users = await users_collection.count_documents({
            "created_at": {"$gte": cohort_start},
            "last_login": {"$gte": week_ago}
        })
        
        retention_rate = (retained_users / cohort_users * 100) if cohort_users > 0 else 0
        
        return {
            "cohort_period_days": cohort_days,
            "cohort_users": cohort_users,
            "retained_users": retained_users,
            "retention_rate": f"{retention_rate:.2f}%"
        }
    
    # ============================================
    # TRADING ANALYTICS
    # ============================================
    
    async def get_trading_volume(self, days: int = 30) -> dict:
        """Get trading volume metrics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        orders_collection = self.db.get_collection("orders")
        
        # Total trades
        total_trades = await orders_collection.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Trading volume
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}, "status": "filled"}},
            {"$group": {
                "_id": None,
                "total_volume": {"$sum": {"$multiply": ["$amount", "$price"]}},
                "avg_trade_size": {"$avg": {"$multiply": ["$amount", "$price"]}},
                "buy_volume": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$side", "buy"]},
                            {"$multiply": ["$amount", "$price"]},
                            0
                        ]
                    }
                },
                "sell_volume": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$side", "sell"]},
                            {"$multiply": ["$amount", "$price"]},
                            0
                        ]
                    }
                }
            }}
        ]
        
        result = await orders_collection.aggregate(pipeline).to_list(1)
        volume_data = result[0] if result else {
            "total_volume": 0,
            "avg_trade_size": 0,
            "buy_volume": 0,
            "sell_volume": 0
        }
        
        # Most traded pairs
        pipeline_pairs = [
            {"$match": {"created_at": {"$gte": start_date}, "status": "filled"}},
            {"$group": {
                "_id": "$trading_pair",
                "volume": {"$sum": {"$multiply": ["$amount", "$price"]}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"volume": -1}},
            {"$limit": 10}
        ]
        
        top_pairs = await orders_collection.aggregate(pipeline_pairs).to_list(10)
        
        # Daily trading volume
        pipeline_daily = [
            {"$match": {"created_at": {"$gte": start_date}, "status": "filled"}},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "volume": {"$sum": {"$multiply": ["$amount", "$price"]}},
                "trades": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_volume = await orders_collection.aggregate(pipeline_daily).to_list(days)
        
        return {
            "period_days": days,
            "total_trades": total_trades,
            "total_volume": round(volume_data["total_volume"], 2),
            "avg_trade_size": round(volume_data["avg_trade_size"], 2),
            "buy_volume": round(volume_data["buy_volume"], 2),
            "sell_volume": round(volume_data["sell_volume"], 2),
            "top_trading_pairs": top_pairs,
            "daily_volume": daily_volume
        }
    
    # ============================================
    # REVENUE ANALYTICS
    # ============================================
    
    async def get_revenue_metrics(self, days: int = 30) -> dict:
        """Calculate revenue from trading fees, withdrawal fees, etc."""
        start_date = datetime.utcnow() - timedelta(days=days)
        transactions_collection = self.db.get_collection("transactions")
        
        # Trading fees
        pipeline_fees = [
            {"$match": {
                "type": "fee",
                "created_at": {"$gte": start_date}
            }},
            {"$group": {
                "_id": None,
                "total_fees": {"$sum": {"$abs": "$amount"}},
                "count": {"$sum": 1}
            }}
        ]
        
        fee_result = await transactions_collection.aggregate(pipeline_fees).to_list(1)
        fee_data = fee_result[0] if fee_result else {"total_fees": 0, "count": 0}
        
        # Withdrawal fees
        withdrawals_collection = self.db.get_collection("withdrawals")
        pipeline_withdrawal_fees = [
            {"$match": {
                "created_at": {"$gte": start_date},
                "status": {"$in": ["completed", "processing"]}
            }},
            {"$group": {
                "_id": None,
                "total_fees": {"$sum": "$fee"},
                "count": {"$sum": 1}
            }}
        ]
        
        withdrawal_fee_result = await withdrawals_collection.aggregate(pipeline_withdrawal_fees).to_list(1)
        withdrawal_fee_data = withdrawal_fee_result[0] if withdrawal_fee_result else {"total_fees": 0, "count": 0}
        
        total_revenue = fee_data["total_fees"] + withdrawal_fee_data["total_fees"]
        
        # Daily revenue breakdown
        pipeline_daily = [
            {"$match": {
                "type": "fee",
                "created_at": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "revenue": {"$sum": {"$abs": "$amount"}}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_revenue = await transactions_collection.aggregate(pipeline_daily).to_list(days)
        
        return {
            "period_days": days,
            "total_revenue": round(total_revenue, 2),
            "trading_fees": round(fee_data["total_fees"], 2),
            "withdrawal_fees": round(withdrawal_fee_data["total_fees"], 2),
            "trading_fee_count": fee_data["count"],
            "withdrawal_fee_count": withdrawal_fee_data["count"],
            "avg_revenue_per_day": round(total_revenue / days, 2) if days > 0 else 0,
            "daily_revenue": daily_revenue
        }
    
    # ============================================
    # CONVERSION FUNNEL ANALYTICS
    # ============================================
    
    async def get_conversion_funnel(self, days: int = 30) -> dict:
        """Analyze user conversion funnel."""
        start_date = datetime.utcnow() - timedelta(days=days)
        users_collection = self.db.get_collection("users")
        deposits_collection = self.db.get_collection("deposits")
        orders_collection = self.db.get_collection("orders")
        
        # Stage 1: Signups
        signups = await users_collection.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Stage 2: Email verification
        verified = await users_collection.count_documents({
            "created_at": {"$gte": start_date},
            "email_verified": True
        })
        
        # Stage 3: First deposit
        users_with_deposits_pipeline = [
            {"$match": {
                "created_at": {"$gte": start_date},
                "status": {"$in": ["finished", "confirmed"]}
            }},
            {"$group": {"_id": "$user_id"}},
            {"$count": "count"}
        ]
        
        depositors_result = await deposits_collection.aggregate(users_with_deposits_pipeline).to_list(1)
        depositors = depositors_result[0]["count"] if depositors_result else 0
        
        # Stage 4: First trade
        users_with_trades_pipeline = [
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }},
            {"$match": {
                "user.created_at": {"$gte": start_date},
                "status": "filled"
            }},
            {"$group": {"_id": "$user_id"}},
            {"$count": "count"}
        ]
        
        traders_result = await orders_collection.aggregate(users_with_trades_pipeline).to_list(1)
        traders = traders_result[0]["count"] if traders_result else 0
        
        # Calculate conversion rates
        verification_rate = (verified / signups * 100) if signups > 0 else 0
        deposit_rate = (depositors / verified * 100) if verified > 0 else 0
        trading_rate = (traders / depositors * 100) if depositors > 0 else 0
        overall_rate = (traders / signups * 100) if signups > 0 else 0
        
        return {
            "period_days": days,
            "funnel": [
                {"stage": "Signups", "count": signups, "rate": "100%"},
                {"stage": "Email Verified", "count": verified, "rate": f"{verification_rate:.2f}%"},
                {"stage": "First Deposit", "count": depositors, "rate": f"{deposit_rate:.2f}%"},
                {"stage": "First Trade", "count": traders, "rate": f"{trading_rate:.2f}%"}
            ],
            "overall_conversion_rate": f"{overall_rate:.2f}%"
        }
    
    # ============================================
    # PERFORMANCE METRICS
    # ============================================
    
    async def get_performance_metrics(self) -> dict:
        """Get system performance metrics."""
        # Database performance
        users_collection = self.db.get_collection("users")
        orders_collection = self.db.get_collection("orders")
        
        # Collection sizes
        total_users = await users_collection.count_documents({})
        total_orders = await orders_collection.count_documents({})
        
        # Recent activity (last hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_orders = await orders_collection.count_documents({
            "created_at": {"$gte": hour_ago}
        })
        
        return {
            "database": {
                "total_users": total_users,
                "total_orders": total_orders,
                "orders_last_hour": recent_orders
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ============================================
    # COMPREHENSIVE DASHBOARD
    # ============================================
    
    async def get_dashboard_metrics(self, days: int = 30) -> dict:
        """Get comprehensive metrics for admin dashboard."""
        user_growth = await self.get_user_growth(days)
        trading_volume = await self.get_trading_volume(days)
        revenue = await self.get_revenue_metrics(days)
        funnel = await self.get_conversion_funnel(days)
        performance = await self.get_performance_metrics()
        
        return {
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "user_metrics": user_growth,
            "trading_metrics": trading_volume,
            "revenue_metrics": revenue,
            "conversion_funnel": funnel,
            "performance": performance
        }


# Analytics helper functions for easy access
async def track_event(db: AsyncIOMotorDatabase, event_type: str, user_id: Optional[str], metadata: Optional[dict] = None):
    """Track custom analytics event."""
    events_collection = db.get_collection("analytics_events")
    
    event = {
        "type": event_type,
        "user_id": user_id,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow()
    }
    
    await events_collection.insert_one(event)
    logger.debug(f"📊 Event tracked: {event_type}")


async def create_analytics_indexes(db: AsyncIOMotorDatabase):
    """Create indexes for analytics collections."""
    from pymongo import ASCENDING, DESCENDING
    
    events_collection = db.get_collection("analytics_events")
    
    # Event analytics indexes
    await events_collection.create_index([
        ("type", ASCENDING),
        ("timestamp", DESCENDING)
    ])
    
    await events_collection.create_index([
        ("user_id", ASCENDING),
        ("timestamp", DESCENDING)
    ])
    
    # TTL index (delete events after 90 days)
    await events_collection.create_index(
        [("timestamp", ASCENDING)],
        expireAfterSeconds=90 * 24 * 60 * 60
    )
    
    logger.info("✅ Analytics indexes created")
