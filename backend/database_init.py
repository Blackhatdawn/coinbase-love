"""
Database Initialization and Schema Management
Creates all necessary collections, indexes, and constraints for CryptoVault
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)


async def create_database_indexes():
    """
    Create all database indexes for optimal performance and data integrity.
    Run this during application startup or as a maintenance script.
    """
    
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    
    logger.info("🔨 Creating database indexes...")
    
    try:
        # ============================================
        # USERS COLLECTION
        # ============================================
        users = db.get_collection("users")
        
        # Unique email index
        await users.create_index("email", unique=True, name="idx_users_email_unique")
        
        # Performance indexes
        await users.create_index("last_login", name="idx_users_last_login")
        await users.create_index("created_at", name="idx_users_created_at")
        await users.create_index("email_verified", name="idx_users_email_verified")
        
        # Compound index for authentication queries
        await users.create_index(
            [("email", 1), ("email_verified", 1)],
            name="idx_users_email_verified"
        )
        
        logger.info("✅ Users indexes created")
        
        # ============================================
        # PORTFOLIOS COLLECTION
        # ============================================
        portfolios = db.get_collection("portfolios")
        
        # Unique user_id index
        await portfolios.create_index("user_id", unique=True, name="idx_portfolios_user_unique")
        await portfolios.create_index("created_at", name="idx_portfolios_created_at")
        await portfolios.create_index("updated_at", name="idx_portfolios_updated_at")
        
        logger.info("✅ Portfolios indexes created")
        
        # ============================================
        # ORDERS COLLECTION
        # ============================================
        orders = db.get_collection("orders")
        
        # User queries
        await orders.create_index("user_id", name="idx_orders_user_id")
        await orders.create_index("created_at", name="idx_orders_created_at")
        await orders.create_index("status", name="idx_orders_status")
        
        # Compound indexes for efficient queries
        await orders.create_index(
            [("user_id", 1), ("status", 1), ("created_at", -1)],
            name="idx_orders_user_status_date"
        )
        await orders.create_index(
            [("user_id", 1), ("trading_pair", 1)],
            name="idx_orders_user_pair"
        )
        
        logger.info("✅ Orders indexes created")
        
        # ============================================
        # TRANSACTIONS COLLECTION
        # ============================================
        transactions = db.get_collection("transactions")
        
        await transactions.create_index("user_id", name="idx_transactions_user_id")
        await transactions.create_index("type", name="idx_transactions_type")
        await transactions.create_index("created_at", name="idx_transactions_created_at")
        await transactions.create_index("status", name="idx_transactions_status")
        await transactions.create_index("reference", name="idx_transactions_reference")
        
        # Compound indexes
        await transactions.create_index(
            [("user_id", 1), ("type", 1), ("created_at", -1)],
            name="idx_transactions_user_type_date"
        )
        await transactions.create_index(
            [("user_id", 1), ("status", 1)],
            name="idx_transactions_user_status"
        )
        
        logger.info("✅ Transactions indexes created")
        
        # ============================================
        # WALLETS COLLECTION
        # ============================================
        wallets = db.get_collection("wallets")
        
        await wallets.create_index("user_id", unique=True, name="idx_wallets_user_unique")
        await wallets.create_index("created_at", name="idx_wallets_created_at")
        await wallets.create_index("updated_at", name="idx_wallets_updated_at")
        
        logger.info("✅ Wallets indexes created")
        
        # ============================================
        # DEPOSITS COLLECTION
        # ============================================
        deposits = db.get_collection("deposits")
        
        await deposits.create_index("user_id", name="idx_deposits_user_id")
        await deposits.create_index("order_id", unique=True, name="idx_deposits_order_unique")
        await deposits.create_index("payment_id", name="idx_deposits_payment_id")
        await deposits.create_index("status", name="idx_deposits_status")
        await deposits.create_index("created_at", name="idx_deposits_created_at")
        
        # Compound indexes
        await deposits.create_index(
            [("user_id", 1), ("status", 1), ("created_at", -1)],
            name="idx_deposits_user_status_date"
        )
        
        # TTL index for expired deposits (auto-delete after 7 days)
        await deposits.create_index(
            "expires_at",
            name="idx_deposits_ttl",
            expireAfterSeconds=7*24*60*60  # 7 days
        )
        
        logger.info("✅ Deposits indexes created")
        
        # ============================================
        # WITHDRAWALS COLLECTION
        # ============================================
        withdrawals = db.get_collection("withdrawals")
        
        await withdrawals.create_index("user_id", name="idx_withdrawals_user_id")
        await withdrawals.create_index("status", name="idx_withdrawals_status")
        await withdrawals.create_index("created_at", name="idx_withdrawals_created_at")
        await withdrawals.create_index(
            [("user_id", 1), ("status", 1), ("created_at", -1)],
            name="idx_withdrawals_user_status_date"
        )
        
        logger.info("✅ Withdrawals indexes created")
        
        # ============================================
        # PRICE ALERTS COLLECTION
        # ============================================
        alerts = db.get_collection("price_alerts")
        
        await alerts.create_index("user_id", name="idx_alerts_user_id")
        await alerts.create_index("symbol", name="idx_alerts_symbol")
        await alerts.create_index("is_active", name="idx_alerts_active")
        await alerts.create_index("created_at", name="idx_alerts_created_at")
        
        # Compound indexes for alert checking
        await alerts.create_index(
            [("symbol", 1), ("is_active", 1)],
            name="idx_alerts_symbol_active"
        )
        await alerts.create_index(
            [("user_id", 1), ("is_active", 1)],
            name="idx_alerts_user_active"
        )
        
        logger.info("✅ Price alerts indexes created")
        
        # ============================================
        # AUDIT LOGS COLLECTION
        # ============================================
        audit_logs = db.get_collection("audit_logs")
        
        await audit_logs.create_index("user_id", name="idx_audit_user_id")
        await audit_logs.create_index("action", name="idx_audit_action")
        await audit_logs.create_index("timestamp", name="idx_audit_timestamp")
        await audit_logs.create_index("resource", name="idx_audit_resource")
        
        # Compound indexes for audit queries
        await audit_logs.create_index(
            [("user_id", 1), ("timestamp", -1)],
            name="idx_audit_user_time"
        )
        await audit_logs.create_index(
            [("action", 1), ("timestamp", -1)],
            name="idx_audit_action_time"
        )
        
        # TTL index (auto-delete audit logs older than 90 days)
        await audit_logs.create_index(
            "timestamp",
            name="idx_audit_ttl",
            expireAfterSeconds=90*24*60*60  # 90 days
        )
        
        logger.info("✅ Audit logs indexes created")
        
        # ============================================
        # LOGIN ATTEMPTS COLLECTION
        # ============================================
        login_attempts = db.get_collection("login_attempts")
        
        await login_attempts.create_index("user_id", name="idx_login_user_id")
        await login_attempts.create_index("email", name="idx_login_email")
        await login_attempts.create_index("timestamp", name="idx_login_timestamp")
        await login_attempts.create_index("success", name="idx_login_success")
        
        # TTL index (auto-delete after 30 days)
        await login_attempts.create_index(
            "timestamp",
            name="idx_login_ttl",
            expireAfterSeconds=30*24*60*60  # 30 days
        )
        
        logger.info("✅ Login attempts indexes created")
        
        # ============================================
        # BLACKLISTED TOKENS COLLECTION
        # ============================================
        blacklisted = db.get_collection("blacklisted_tokens")
        
        await blacklisted.create_index("token", unique=True, name="idx_blacklist_token_unique")
        
        # TTL index (tokens expire automatically)
        await blacklisted.create_index(
            "expires_at",
            name="idx_blacklist_ttl",
            expireAfterSeconds=0
        )
        
        logger.info("✅ Blacklisted tokens indexes created")
        
        # ============================================
        # SESSIONS COLLECTION (optional)
        # ============================================
        sessions = db.get_collection("sessions")
        
        await sessions.create_index("user_id", name="idx_sessions_user_id")
        await sessions.create_index("session_id", unique=True, name="idx_sessions_id_unique")
        await sessions.create_index("created_at", name="idx_sessions_created_at")
        
        # TTL index (auto-delete expired sessions)
        await sessions.create_index(
            "expires_at",
            name="idx_sessions_ttl",
            expireAfterSeconds=0
        )
        
        logger.info("✅ Sessions indexes created")
        
        # ============================================
        # NOTIFICATIONS COLLECTION
        # ============================================
        notifications = db.get_collection("notifications")
        
        await notifications.create_index("user_id", name="idx_notifications_user_id")
        await notifications.create_index("read", name="idx_notifications_read")
        await notifications.create_index("created_at", name="idx_notifications_created_at")
        
        # Compound index for unread notifications
        await notifications.create_index(
            [("user_id", 1), ("read", 1), ("created_at", -1)],
            name="idx_notifications_user_unread"
        )
        
        # TTL index (auto-delete old notifications after 90 days)
        await notifications.create_index(
            "created_at",
            name="idx_notifications_ttl",
            expireAfterSeconds=90*24*60*60  # 90 days
        )
        
        logger.info("✅ Notifications indexes created")
        
        logger.info("=" * 70)
        logger.info("🎉 All database indexes created successfully!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {str(e)}")
        raise
    finally:
        client.close()


async def create_default_data():
    """Create default/seed data for the application."""
    
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    
    logger.info("🌱 Creating default data...")
    
    try:
        # Add any default data here (e.g., admin user, default settings, etc.)
        logger.info("✅ Default data created")
        
    except Exception as e:
        logger.error(f"❌ Error creating default data: {str(e)}")
        raise
    finally:
        client.close()


async def verify_database_setup():
    """Verify database connection and collections."""
    
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    
    logger.info("🔍 Verifying database setup...")
    
    try:
        # Test connection
        await client.admin.command('ping')
        logger.info("✅ Database connection successful")
        
        # List collections
        collections = await db.list_collection_names()
        logger.info(f"📦 Collections: {', '.join(collections)}")
        
        # Verify indexes
        for collection_name in collections:
            collection = db.get_collection(collection_name)
            indexes = await collection.index_information()
            logger.info(f"   {collection_name}: {len(indexes)} indexes")
        
        logger.info("✅ Database verification complete")
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {str(e)}")
        raise
    finally:
        client.close()


async def main():
    """Main function to run database initialization."""
    print("\n" + "=" * 70)
    print("🚀 CryptoVault Database Initialization")
    print("=" * 70 + "\n")
    
    try:
        # Create indexes
        await create_database_indexes()
        
        # Create default data
        await create_default_data()
        
        # Verify setup
        await verify_database_setup()
        
        print("\n" + "=" * 70)
        print("✅ Database initialization completed successfully!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {str(e)}\n")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
