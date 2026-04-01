"""
Mock Database Connection for testing in environments without real MongoDB.
Uses mongomock-motor for in-memory MongoDB simulation.
"""

import logging
from typing import Optional, Dict, Any
from mongomock_motor import AsyncMongoMockClient

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Mock MongoDB connection using mongomock-motor."""

    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        **kwargs
    ):
        self.mongo_url = mongo_url
        self.db_name = db_name.strip()
        self.client = AsyncMongoMockClient()
        self.db = self.client[self.db_name]
        self._is_connected = True
        logger.info(f"✅ Mock MongoDB initialized (database: {self.db_name})")

    async def connect(self, **kwargs):
        self._is_connected = True
        return

    async def health_check(self) -> bool:
        return True

    async def disconnect(self):
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def get_collection(self, collection_name: str):
        return self.db[collection_name]

    async def __aenter__(self) -> "DatabaseConnection":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Compatible with original API
db_connection: Optional[DatabaseConnection] = None

async def get_database() -> DatabaseConnection:
    if db_connection is None:
        raise RuntimeError("Mock Database not initialized.")
    return db_connection

async def initialize_database(mongo_url, db_name, **kwargs):
    global db_connection
    db_connection = DatabaseConnection(mongo_url, db_name)
    return db_connection

async def close_database():
    global db_connection
    db_connection = None
