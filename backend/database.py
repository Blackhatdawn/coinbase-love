"""
Production-ready MongoDB connection module with health checks, retries, exponential backoff,
context manager support, validation, timeouts, and improved error handling/cleanup.
Uses Motor for async operations. Fully compatible with MongoDB Atlas.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MongoDB connection with health checks, retries, and graceful cleanup."""

    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        max_pool_size: int = 50,
        min_pool_size: int = 10,
        server_selection_timeout_ms: int = 5000,
        base_retry_delay: float = 2.0,
        client_options: Optional[Dict[str, Any]] = None,
        # FIX #1: Add default timeout for all database operations (10 seconds)
        default_query_timeout_ms: int = 10000,
    ):
        if not mongo_url:
            raise ValueError("mongo_url is required")
        if not db_name or not db_name.strip():
            raise ValueError("db_name is required and cannot be empty")

        if not (mongo_url.startswith("mongodb://") or mongo_url.startswith("mongodb+srv://")):
            raise ValueError("mongo_url must start with mongodb:// or mongodb+srv://")

        self.mongo_url = mongo_url
        self.db_name = db_name.strip()
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.server_selection_timeout_ms = server_selection_timeout_ms
        self.base_retry_delay = base_retry_delay
        self.client_options = client_options or {}
        # FIX #1: Store default query timeout for database operations
        self.default_query_timeout_ms = default_query_timeout_ms

        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False

    def _cleanup(self):
        """Internal cleanup of client state."""
        self.client = None
        self.db = None
        self._is_connected = False

    async def connect(
        self,
        max_retries: int = 5,
        base_retry_delay: Optional[float] = None,
    ):
        """
        Establish database connection with health check, retries, and exponential backoff.

        If a client already exists, it will first verify the connection health.
        """
        base_retry_delay = base_retry_delay or self.base_retry_delay

        # Check existing connection health if client exists
        if self.client:
            try:
                await asyncio.wait_for(self.client.admin.command("ping"), timeout=5.0)
                if self._is_connected:
                    logger.info("✅ MongoDB connection is already healthy.")
                    return
            except Exception as e:
                logger.warning(f"⚠️ Existing connection unhealthy ({str(e)}). Reconnecting...")
                await self.disconnect()

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔌 Attempting MongoDB connection (attempt {attempt}/{max_retries})...")

                # FIX #1: Add default query timeout to client options
                client_options_with_timeout = {
                    **self.client_options,
                    # Set socket timeout to prevent indefinite hangs on queries
                    "socketTimeoutMS": self.default_query_timeout_ms,
                }

                self.client = AsyncIOMotorClient(
                    self.mongo_url,
                    maxPoolSize=self.max_pool_size,
                    minPoolSize=self.min_pool_size,
                    serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                    retryWrites=True,
                    retryReads=True,
                    **client_options_with_timeout,
                )

                self.db = self.client[self.db_name]

                # Health check with timeout
                await asyncio.wait_for(self.health_check(), timeout=10.0)

                self._is_connected = True
                logger.info(f"✅ MongoDB connected successfully to database: {self.db_name}")
                logger.debug(f"Pool size: {self.min_pool_size}-{self.max_pool_size}")
                logger.debug(f"Server selection timeout: {self.server_selection_timeout_ms}ms")
                logger.debug(f"Default query timeout: {self.default_query_timeout_ms}ms")
                return

            except (ConnectionFailure, ServerSelectionTimeoutError, asyncio.TimeoutError) as e:
                logger.error(f"❌ Connection failed (attempt {attempt}/{max_retries}): {str(e)}")
                self._cleanup()

                if attempt < max_retries:
                    delay = base_retry_delay * (2 ** (attempt - 1))
                    logger.info(f"⏳ Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.critical("💥 Failed to connect to MongoDB after all retries")
                    raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")

            except Exception as e:
                logger.critical(f"💥 Unexpected error during connection: {str(e)}")
                self._cleanup()
                raise

    async def health_check(self) -> bool:
        """Perform a ping health check on the MongoDB server."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        try:
            await self.client.admin.command("ping")
            logger.debug("✅ MongoDB health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB health check failed: {str(e)}")
            self._is_connected = False
            raise

    async def disconnect(self):
        """Gracefully close the database connection."""
        if self.client:
            logger.info("🔌 Closing MongoDB connection...")
            self.client.close()
            self._cleanup()
            logger.info("✅ MongoDB connection closed")

    @property
    def is_connected(self) -> bool:
        """Quick flag-based check if the database appears connected."""
        return self._is_connected and (self.client is not None) and (self.db is not None)

    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if self.db is None or not self._is_connected:
            raise RuntimeError("Database not connected. Call connect() first or use async context manager.")
        return self.db[collection_name]

    # Async context manager support (optional but useful)
    async def __aenter__(self) -> "DatabaseConnection":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


# Global singleton (compatible with your existing initialize_database/get_database)
db_connection: Optional[DatabaseConnection] = None


async def get_database() -> DatabaseConnection:
    """Get the global database connection instance."""
    if db_connection is None or not db_connection.is_connected:
        raise RuntimeError("Database not initialized or not connected. Call initialize_database() first.")
    return db_connection


async def initialize_database(
    mongo_url: str,
    db_name: str,
    max_pool_size: int = 50,
    min_pool_size: int = 10,
    server_selection_timeout_ms: int = 5000,
    base_retry_delay: float = 2.0,
    client_options: Optional[Dict[str, Any]] = None,
    **connect_kwargs,
):
    """
    Initialize and connect the global database instance.
    
    client_options can include tls=True, tlsAllowInvalidCertificates=False, etc. (useful for Atlas).
    """
    global db_connection
    db_connection = DatabaseConnection(
        mongo_url=mongo_url,
        db_name=db_name,
        max_pool_size=max_pool_size,
        min_pool_size=min_pool_size,
        server_selection_timeout_ms=server_selection_timeout_ms,
        base_retry_delay=base_retry_delay,
        client_options=client_options,
    )
    await db_connection.connect(**connect_kwargs)
    return db_connection


async def close_database():
    """Close the global database connection."""
    global db_connection
    if db_connection:
        await db_connection.disconnect()
        db_connection = None
