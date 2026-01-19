"""
MongoDB Indexes - Performance Optimization
Create indexes for frequently queried fields
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "cryptovault_db")


async def create_indexes():
    """Create all required indexes for optimal query performance"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔧 Creating MongoDB indexes...")
    
    try:
        # ============================================
        # USERS COLLECTION
        # ============================================
        print("\n📁 Users indexes...")
        await db.users.create_index("email", unique=True)
        await db.users.create_index("created_at")
        await db.users.create_index([("email_verified", 1), ("created_at", -1)])
        print("✅ Users: email (unique), created_at, email_verified+created_at")
        
        # ============================================
        # PORTFOLIO COLLECTION
        # ============================================
        print("\n📁 Portfolio indexes...")
        await db.portfolio.create_index("user_id", unique=True)
        await db.portfolio.create_index([("user_id", 1), ("updated_at", -1)])
        print("✅ Portfolio: user_id (unique), user_id+updated_at")
        
        # ============================================
        # TRANSACTIONS COLLECTION
        # ============================================
        print("\n📁 Transactions indexes...")
        await db.transactions.create_index([("user_id", 1), ("created_at", -1)])
        await db.transactions.create_index([("user_id", 1), ("type", 1), ("created_at", -1)])
        await db.transactions.create_index("transaction_hash")
        await db.transactions.create_index("status")
        print("✅ Transactions: user_id+created_at, user_id+type+created_at, transaction_hash, status")
        
        # ============================================
        # ORDERS COLLECTION
        # ============================================
        print("\n📁 Orders indexes...")
        await db.orders.create_index([("user_id", 1), ("created_at", -1)])
        await db.orders.create_index([("user_id", 1), ("status", 1)])
        await db.orders.create_index("trading_pair")
        await db.orders.create_index("status")
        print("✅ Orders: user_id+created_at, user_id+status, trading_pair, status")
        
        # ============================================
        # ALERTS COLLECTION
        # ============================================
        print("\n📁 Alerts indexes...")
        await db.alerts.create_index([("user_id", 1), ("is_active", 1)])
        await db.alerts.create_index([("symbol", 1), ("is_active", 1)])
        await db.alerts.create_index("created_at")
        print("✅ Alerts: user_id+is_active, symbol+is_active, created_at")
        
        # ============================================
        # STAKES COLLECTION
        # ============================================
        print("\n📁 Stakes indexes...")
        await db.stakes.create_index([("user_id", 1), ("status", 1)])
        await db.stakes.create_index([("user_id", 1), ("created_at", -1)])
        await db.stakes.create_index("status")
        print("✅ Stakes: user_id+status, user_id+created_at, status")
        
        # ============================================
        # REFERRALS COLLECTION
        # ============================================
        print("\n📁 Referrals indexes...")
        await db.referrals.create_index("referrer_id")
        await db.referrals.create_index("referred_id", unique=True)
        await db.referrals.create_index([("referrer_id", 1), ("created_at", -1)])
        print("✅ Referrals: referrer_id, referred_id (unique), referrer_id+created_at")
        
        # ============================================
        # DEPOSITS COLLECTION
        # ============================================
        print("\n📁 Deposits indexes...")
        await db.deposits.create_index([("user_id", 1), ("created_at", -1)])
        await db.deposits.create_index("order_id", unique=True, sparse=True)
        await db.deposits.create_index("status")
        print("✅ Deposits: user_id+created_at, order_id (unique, sparse), status")
        
        # ============================================
        # WITHDRAWALS COLLECTION
        # ============================================
        print("\n📁 Withdrawals indexes...")
        await db.withdrawals.create_index([("user_id", 1), ("created_at", -1)])
        await db.withdrawals.create_index([("status", 1), ("created_at", -1)])
        await db.withdrawals.create_index("withdrawal_id", unique=True)
        print("✅ Withdrawals: user_id+created_at, status+created_at, withdrawal_id (unique)")
        
        # ============================================
        # TRANSFERS COLLECTION (P2P)
        # ============================================
        print("\n📁 Transfers indexes...")
        await db.transfers.create_index([("sender_id", 1), ("created_at", -1)])
        await db.transfers.create_index([("recipient_id", 1), ("created_at", -1)])
        await db.transfers.create_index("transfer_id", unique=True)
        print("✅ Transfers: sender_id+created_at, recipient_id+created_at, transfer_id (unique)")
        
        # ============================================
        # NOTIFICATIONS COLLECTION
        # ============================================
        print("\n📁 Notifications indexes...")
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.notifications.create_index([("user_id", 1), ("is_read", 1)])
        print("✅ Notifications: user_id+created_at, user_id+is_read")
        
        # ============================================
        # AUDIT LOGS COLLECTION
        # ============================================
        print("\n📁 Audit logs indexes...")
        await db.audit_logs.create_index([("user_id", 1), ("timestamp", -1)])
        await db.audit_logs.create_index([("action", 1), ("timestamp", -1)])
        await db.audit_logs.create_index("timestamp")
        print("✅ Audit logs: user_id+timestamp, action+timestamp, timestamp")
        
        # ============================================
        # VERIFICATION TOKENS COLLECTION
        # ============================================
        print("\n📁 Verification tokens indexes...")
        await db.verification_tokens.create_index("token", unique=True)
        await db.verification_tokens.create_index("email")
        await db.verification_tokens.create_index("expires_at")
        print("✅ Verification tokens: token (unique), email, expires_at")
        
        # ============================================
        # PASSWORD RESET TOKENS COLLECTION
        # ============================================
        print("\n📁 Password reset tokens indexes...")
        await db.password_reset_tokens.create_index("token", unique=True)
        await db.password_reset_tokens.create_index("email")
        await db.password_reset_tokens.create_index("expires_at")
        print("✅ Password reset tokens: token (unique), email, expires_at")
        
        print("\n" + "="*50)
        print("✅ All indexes created successfully!")
        print("="*50)
        
        # List all indexes
        print("\n📊 Index Summary:")
        for collection_name in await db.list_collection_names():
            if not collection_name.startswith('system.'):
                indexes = await db[collection_name].index_information()
                print(f"  {collection_name}: {len(indexes)} indexes")
        
    except Exception as e:
        print(f"\n❌ Error creating indexes: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
