"""
Database index creation for optimized query performance.
Creates compound indexes based on common query patterns.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT

logger = logging.getLogger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase):
    """
    Create all necessary indexes for optimal query performance.
    
    Compound indexes are optimized for:
    - Common filter combinations
    - Sort operations
    - Lookup speed
    - TTL-based cleanup
    """
    logger.info("🔧 Creating database indexes...")
    
    try:
        # ============================================
        # USERS COLLECTION
        # ============================================
        users_collection = db.get_collection("users")
        
        # Unique indexes
        await users_collection.create_index([("email", ASCENDING)], unique=True)
        await users_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Query optimization indexes
        await users_collection.create_index([("email_verified", ASCENDING)])
        await users_collection.create_index([("is_admin", ASCENDING)])
        await users_collection.create_index([("last_login", DESCENDING)])
        await users_collection.create_index([("created_at", DESCENDING)])
        
        # Compound index for locked accounts
        await users_collection.create_index([
            ("locked_until", ASCENDING),
            ("failed_login_attempts", ASCENDING)
        ])

        # Token lookup indexes (email verification & password reset)
        await users_collection.create_index(
            [("email_verification_token", ASCENDING)],
            sparse=True
        )
        await users_collection.create_index(
            [("email_verification_code", ASCENDING)],
            sparse=True
        )
        await users_collection.create_index(
            [("password_reset_token", ASCENDING)],
            sparse=True
        )

        # TTL indexes for temporary tokens
        await users_collection.create_index(
            [("email_verification_expires", ASCENDING)],
            expireAfterSeconds=0,
            partialFilterExpression={"email_verification_expires": {"$type": "date"}}
        )
        await users_collection.create_index(
            [("password_reset_expires", ASCENDING)],
            expireAfterSeconds=0,
            partialFilterExpression={"password_reset_expires": {"$type": "date"}}
        )
        
        logger.info("✅ Users indexes created")
        
        # ============================================
        # WALLETS COLLECTION
        # ============================================
        wallets_collection = db.get_collection("wallets")
        
        await wallets_collection.create_index([("user_id", ASCENDING)], unique=True)
        await wallets_collection.create_index([("id", ASCENDING)], unique=True)
        await wallets_collection.create_index([("updated_at", DESCENDING)])
        
        logger.info("✅ Wallets indexes created")
        
        # ============================================
        # ORDERS COLLECTION
        # ============================================
        orders_collection = db.get_collection("orders")
        
        await orders_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound indexes for user order queries
        await orders_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await orders_collection.create_index([
            ("user_id", ASCENDING),
            ("status", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await orders_collection.create_index([
            ("user_id", ASCENDING),
            ("trading_pair", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # Index for pending orders (for advanced order execution)
        await orders_collection.create_index([
            ("status", ASCENDING),
            ("order_type", ASCENDING),
            ("trading_pair", ASCENDING)
        ])
        
        # TTL index for expired orders
        await orders_collection.create_index(
            [("expire_time", ASCENDING)],
            expireAfterSeconds=0,
            partialFilterExpression={"expire_time": {"$exists": True}}
        )
        
        logger.info("✅ Orders indexes created")
        
        # ============================================
        # TRANSACTIONS COLLECTION
        # ============================================
        transactions_collection = db.get_collection("transactions")
        
        await transactions_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound index for user transaction history
        await transactions_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await transactions_collection.create_index([
            ("user_id", ASCENDING),
            ("type", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await transactions_collection.create_index([
            ("user_id", ASCENDING),
            ("currency", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # Index for transaction references
        await transactions_collection.create_index([("reference", ASCENDING)])
        
        logger.info("✅ Transactions indexes created")
        
        # ============================================
        # DEPOSITS COLLECTION
        # ============================================
        deposits_collection = db.get_collection("deposits")
        
        await deposits_collection.create_index([("id", ASCENDING)], unique=True)
        await deposits_collection.create_index([("order_id", ASCENDING)], unique=True)
        await deposits_collection.create_index([("payment_id", ASCENDING)])
        
        # Compound index for user deposits
        await deposits_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await deposits_collection.create_index([
            ("user_id", ASCENDING),
            ("status", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # TTL index for expired deposits
        await deposits_collection.create_index(
            [("expires_at", ASCENDING)],
            expireAfterSeconds=0,
            partialFilterExpression={"status": "pending", "expires_at": {"$exists": True}}
        )
        
        logger.info("✅ Deposits indexes created")
        
        # ============================================
        # WITHDRAWALS COLLECTION
        # ============================================
        withdrawals_collection = db.get_collection("withdrawals")
        
        await withdrawals_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound index for user withdrawals
        await withdrawals_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await withdrawals_collection.create_index([
            ("user_id", ASCENDING),
            ("status", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # Admin view: pending withdrawals
        await withdrawals_collection.create_index([
            ("status", ASCENDING),
            ("created_at", ASCENDING)
        ])
        
        logger.info("✅ Withdrawals indexes created")
        
        # ============================================
        # TRANSFERS COLLECTION (P2P)
        # ============================================
        transfers_collection = db.get_collection("transfers")
        
        await transfers_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound index for user transfers (both sent and received)
        await transfers_collection.create_index([
            ("sender_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await transfers_collection.create_index([
            ("recipient_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await transfers_collection.create_index([
            ("status", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        logger.info("✅ Transfers indexes created")
        
        # ============================================
        # PORTFOLIOS COLLECTION
        # ============================================
        portfolios_collection = db.get_collection("portfolios")
        
        await portfolios_collection.create_index([("id", ASCENDING)], unique=True)
        await portfolios_collection.create_index([("user_id", ASCENDING)], unique=True)
        await portfolios_collection.create_index([("updated_at", DESCENDING)])
        
        logger.info("✅ Portfolios indexes created")
        
        # ============================================
        # PRICE ALERTS COLLECTION
        # ============================================
        alerts_collection = db.get_collection("price_alerts")
        
        await alerts_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound index for user alerts
        await alerts_collection.create_index([
            ("user_id", ASCENDING),
            ("is_active", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # Index for active alerts by symbol (for checking triggers)
        await alerts_collection.create_index([
            ("symbol", ASCENDING),
            ("is_active", ASCENDING),
            ("condition", ASCENDING)
        ])
        
        logger.info("✅ Price alerts indexes created")
        
        # ============================================
        # NOTIFICATIONS COLLECTION
        # ============================================
        notifications_collection = db.get_collection("notifications")
        
        await notifications_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound index for user notifications
        await notifications_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await notifications_collection.create_index([
            ("user_id", ASCENDING),
            ("read", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await notifications_collection.create_index([
            ("user_id", ASCENDING),
            ("type", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # TTL index for old notifications (delete after 90 days)
        await notifications_collection.create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
        )
        
        logger.info("✅ Notifications indexes created")
        
        # ============================================
        # AUDIT LOGS COLLECTION
        # ============================================
        audit_logs_collection = db.get_collection("audit_logs")
        
        await audit_logs_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound index for audit log queries
        await audit_logs_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await audit_logs_collection.create_index([
            ("action", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        await audit_logs_collection.create_index([
            ("user_id", ASCENDING),
            ("action", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # Index for resource lookup
        await audit_logs_collection.create_index([("resource", ASCENDING)])
        
        # TTL index for old audit logs (delete after 7 years)
        await audit_logs_collection.create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=7 * 365 * 24 * 60 * 60  # 7 years
        )
        
        logger.info("✅ Audit logs indexes created")
        
        # ============================================
        # LOGIN ATTEMPTS COLLECTION
        # ============================================
        login_attempts_collection = db.get_collection("login_attempts")
        
        await login_attempts_collection.create_index([("id", ASCENDING)], unique=True)
        
        # Compound index for security analysis
        await login_attempts_collection.create_index([
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        await login_attempts_collection.create_index([
            ("ip_address", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        await login_attempts_collection.create_index([
            ("success", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        # TTL index for cleanup (delete after 30 days)
        await login_attempts_collection.create_index(
            [("timestamp", ASCENDING)],
            expireAfterSeconds=30 * 24 * 60 * 60  # 30 days
        )
        
        logger.info("✅ Login attempts indexes created")
        
        # ============================================
        # BLACKLISTED TOKENS COLLECTION
        # ============================================
        blacklisted_tokens_collection = db.get_collection("blacklisted_tokens")
        
        await blacklisted_tokens_collection.create_index([("token", ASCENDING)], unique=True)
        await blacklisted_tokens_collection.create_index(
            [("expires_at", ASCENDING)],
            expireAfterSeconds=0
        )
        
        logger.info("✅ Blacklisted tokens indexes created")
        
        # ============================================
        # SESSIONS COLLECTION
        # ============================================
        sessions_collection = db.get_collection("sessions")
        
        await sessions_collection.create_index([("id", ASCENDING)], unique=True)
        await sessions_collection.create_index([("session_id", ASCENDING)], unique=True)
        
        # Index for user sessions
        await sessions_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        
        # TTL index for expired sessions
        await sessions_collection.create_index(
            [("expires_at", ASCENDING)],
            expireAfterSeconds=0
        )
        
        logger.info("✅ Sessions indexes created")
        
        logger.info("🎉 All database indexes created successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        raise


async def list_indexes(db: AsyncIOMotorDatabase):
    """List all indexes for verification."""
    collections = await db.list_collection_names()
    
    logger.info("📋 Listing all database indexes...")
    
    for collection_name in collections:
        collection = db.get_collection(collection_name)
        indexes = await collection.index_information()
        
        logger.info(f"\n{collection_name}:")
        for index_name, index_info in indexes.items():
            logger.info(f"  - {index_name}: {index_info['key']}")


if __name__ == "__main__":
    # For manual index creation/testing
    import asyncio
    from database import initialize_database
    from config import settings
    
    async def main():
        db_conn = await initialize_database(
            mongo_url=settings.mongo_url,
            db_name=settings.db_name
        )
        
        await create_indexes(db_conn.db)
        await list_indexes(db_conn.db)
        
        await db_conn.disconnect()
    
    asyncio.run(main())
