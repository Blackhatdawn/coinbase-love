"""
MongoDB Connection Pool Manager
Optimizes and monitors database connection reuse and health
Phase 4: Advanced Request Management
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    """Statistics about connection pool"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connection_timeouts: int = 0
    connection_errors: int = 0
    connection_reuses: int = 0
    avg_connection_lifetime_minutes: float = 0.0
    pool_exhaustion_events: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionPoolManager:
    """
    Manages MongoDB connection pooling with health monitoring.
    
    Features:
    - Connection reuse tracking
    - Idle connection cleanup
    - Connection health checks
    - Pool capacity monitoring
    - Statistics and metrics
    - Automatic recovery
    """
    
    def __init__(
        self,
        min_pool_size: int = 5,
        max_pool_size: int = 50,
        max_idle_time_minutes: int = 30
    ):
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.max_idle_time = timedelta(minutes=max_idle_time_minutes)
        
        self.stats = PoolStats()
        self.stats.total_connections = 0
        
        self.connection_history: Dict[int, datetime] = {}  # id -> created_at
        self.last_cleanup = datetime.now(timezone.utc)
        
        logger.info(
            f"🗄️  Connection pool initialized: "
            f"min={min_pool_size}, max={max_pool_size}, "
            f"max_idle={max_idle_time_minutes}m"
        )
    
    def report_connection_acquired(self, connection_id: int):
        """Report that a connection was acquired from pool"""
        if connection_id not in self.connection_history:
            self.connection_history[connection_id] = datetime.now(timezone.utc)
            self.stats.total_connections += 1
        
        self.stats.connection_reuses += 1
        self.stats.active_connections += 1
        if self.stats.idle_connections > 0:
            self.stats.idle_connections -= 1
    
    def report_connection_released(self, connection_id: int):
        """Report that a connection was released back to pool"""
        if self.stats.active_connections > 0:
            self.stats.active_connections -= 1
            self.stats.idle_connections += 1
    
    def report_connection_error(self, connection_id: int):
        """Report a connection error"""
        self.stats.connection_errors += 1
        logger.error(f"❌ Connection {connection_id} failed")
        
        # Remove bad connection
        if connection_id in self.connection_history:
            del self.connection_history[connection_id]
            self.stats.total_connections -= 1
    
    def report_connection_timeout(self, connection_id: int):
        """Report a connection timeout"""
        self.stats.connection_timeouts += 1
        if self.stats.total_connections >= self.max_pool_size:
            self.stats.pool_exhaustion_events += 1
            logger.warning(
                f"⚠️  Pool near exhaustion: {self.stats.active_connections}/"
                f"{self.stats.total_connections} connections active"
            )
    
    async def cleanup_idle_connections(self) -> int:
        """
        Remove idle connections that exceed max idle time.
        But keep at least min_pool_size connections.
        """
        now = datetime.now(timezone.utc)
        to_remove = []
        
        for conn_id, created_at in self.connection_history.items():
            age = now - created_at
            
            # Keep at least min_pool_size connections
            if self.stats.total_connections - len(to_remove) <= self.min_pool_size:
                break
            
            # Remove if idle too long
            if age > self.max_idle_time and self.stats.active_connections < self.stats.total_connections:
                to_remove.append(conn_id)
        
        for conn_id in to_remove:
            del self.connection_history[conn_id]
            self.stats.total_connections -= 1
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} idle connections")
        
        self.last_cleanup = now
        return len(to_remove)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on connection pool.
        """
        # Cleanup expired connections
        await self.cleanup_idle_connections()
        
        health = {
            "pool_size": self.stats.total_connections,
            "active": self.stats.active_connections,
            "idle": self.stats.idle_connections,
            "capacity_used": f"{self.stats.active_connections}/{self.max_pool_size}",
            "connection_errors": self.stats.connection_errors,
            "timeouts": self.stats.connection_timeouts,
            "reuses": self.stats.connection_reuses,
            "pool_exhaustion_events": self.stats.pool_exhaustion_events,
            "healthy": self.stats.connection_errors < 5 and self.stats.timeouts < 3
        }
        
        if not health["healthy"]:
            logger.warning(f"⚠️  Connection pool health degraded: {health}")
        
        return health
    
    async def optimize_pool(self):
        """
        Optimize pool size based on usage patterns.
        """
        # If many timeouts, gradually increase max_pool_size
        if self.stats.pool_exhaustion_events > 10:
            self.max_pool_size = min(self.max_pool_size + 5, 100)
            logger.info(f"📈 Increased max_pool_size to {self.max_pool_size}")
            self.stats.pool_exhaustion_events = 0
        
        # If errors, reduce max_pool_size slightly
        if self.stats.connection_errors > self.stats.connection_reuses * 0.1:  # >10% error rate
            self.max_pool_size = max(self.max_pool_size - 5, self.min_pool_size)
            logger.warning(f"📉 Reduced max_pool_size to {self.max_pool_size} due to errors")
            self.stats.connection_errors = 0  # Reset counter
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        age_minutes = (datetime.now(timezone.utc) - self.stats.created_at).total_seconds() / 60
        avg_lifetime = (
            sum((datetime.now(timezone.utc) - created_at).total_seconds() / 60
                for created_at in self.connection_history.values()) / len(self.connection_history)
            if self.connection_history else 0
        )
        
        return {
            "total_connections": self.stats.total_connections,
            "active_connections": self.stats.active_connections,
            "idle_connections": self.stats.idle_connections,
            "min_pool_size": self.min_pool_size,
            "max_pool_size": self.max_pool_size,
            "capacity_percentage": round(
                (self.stats.active_connections / self.max_pool_size * 100)
                if self.max_pool_size > 0 else 0,
                1
            ),
            "connection_errors": self.stats.connection_errors,
            "connection_timeouts": self.stats.connection_timeouts,
            "connection_reuses": self.stats.connection_reuses,
            "reuse_rate": round(
                self.stats.connection_reuses / self.stats.total_connections
                if self.stats.total_connections > 0 else 0,
                2
            ),
            "avg_connection_lifetime_minutes": round(avg_lifetime, 2),
            "pool_exhaustion_events": self.stats.pool_exhaustion_events,
            "uptime_minutes": round(age_minutes, 2)
        }


# Global singleton
connection_pool_manager = ConnectionPoolManager(
    min_pool_size=5,
    max_pool_size=50,
    max_idle_time_minutes=30
)
