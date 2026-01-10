"""
Database connection module with health checks, retries, and proper error handling.
Production-ready MongoDB connection management.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MongoDB connection with health checks and retries."""
    
    def __init__(self, mongo_url: str, db_name: str, 
                 max_pool_size: int = 50,
                 min_pool_size: int = 10,
                 server_selection_timeout_ms: int = 5000):
        self.mongo_url = mongo_url
        self.db_name = db_name
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.server_selection_timeout_ms = server_selection_timeout_ms
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._is_connected = False
    
    async def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Establish database connection with retries and health check.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay between retries in seconds
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔌 Attempting MongoDB connection (attempt {attempt}/{max_retries})...")
                
                # Create client with connection pooling
                self.client = AsyncIOMotorClient(
                    self.mongo_url,
                    maxPoolSize=self.max_pool_size,
                    minPoolSize=self.min_pool_size,
                    serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                    retryWrites=True,
                    retryReads=True
                )
                
                self.db = self.client[self.db_name]
                
                # Perform health check
                await self.health_check()
                
                self._is_connected = True
                logger.info(f"✅ MongoDB connected successfully to database: {self.db_name}")
                logger.info(f"   Pool size: {self.min_pool_size}-{self.max_pool_size}")
                logger.info(f"   Timeout: {self.server_selection_timeout_ms}ms")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"❌ MongoDB connection failed (attempt {attempt}/{max_retries}): {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.critical("💥 Failed to connect to MongoDB after all retries")
                    raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")
            
            except Exception as e:
                logger.critical(f"💥 Unexpected error during MongoDB connection: {str(e)}")
                raise
    
    async def health_check(self) -> bool:
        """
        Perform health check on MongoDB connection.
        
        Returns:
            bool: True if connection is healthy
        """
        try:
            # Ping the database
            await self.client.admin.command('ping')
            logger.debug("✅ MongoDB health check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ MongoDB health check failed: {str(e)}")
            self._is_connected = False
            raise
    
    async def disconnect(self):
        """Gracefully close database connection."""
        if self.client:
            logger.info("🔌 Closing MongoDB connection...")
            self.client.close()
            self._is_connected = False
            logger.info("✅ MongoDB connection closed")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if not self.db:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.db[collection_name]


# Global database instance
db_connection: Optional[DatabaseConnection] = None


async def get_database() -> DatabaseConnection:
    """Get the global database connection instance."""
    global db_connection
    if not db_connection or not db_connection.is_connected:
        raise RuntimeError("Database not connected")
    return db_connection


async def initialize_database(mongo_url: str, db_name: str, **kwargs):
    """Initialize and connect to database."""
    global db_connection
    db_connection = DatabaseConnection(mongo_url, db_name, **kwargs)
    await db_connection.connect()
    return db_connection


async def close_database():
    """Close database connection."""
    global db_connection
    if db_connection:
        await db_connection.disconnect()
