"""
Monitoring and Metrics for Real-Time Price Stream
Tracks performance, errors, and connection health
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import deque

logger = logging.getLogger(__name__)


class PriceStreamMetrics:
    """Tracks metrics for the price stream service"""
    
    def __init__(self, window_size: int = 3600):
        """
        Initialize metrics tracker.
        
        Args:
            window_size: Number of seconds to keep metrics (default: 1 hour)
        """
        self.window_size = window_size
        
        # Update tracking
        self.updates_received: deque = deque()  # (timestamp, count)
        self.last_update_timestamp = 0
        self.total_updates = 0
        
        # Connection tracking
        self.reconnect_attempts = 0
        self.total_connections = 0
        self.last_connection_time: Optional[datetime] = None
        self.connection_duration = 0
        
        # Error tracking
        self.errors: deque = deque()  # (timestamp, error_type, message)
        self.total_errors = 0
        
        # Performance tracking
        self.message_processing_times: deque = deque()  # (timestamp, duration_ms)
        self.cache_hit_count = 0
        self.cache_miss_count = 0
    
    # ============================================
    # UPDATE METRICS
    # ============================================
    
    def record_price_update(self, count: int = 1, processing_time_ms: float = 0):
        """Record a price update"""
        now = time.time()
        self.updates_received.append((now, count))
        self.total_updates += count
        self.last_update_timestamp = now
        
        if processing_time_ms > 0:
            self.message_processing_times.append((now, processing_time_ms))
        
        self._cleanup_old_data()
    
    # ============================================
    # CONNECTION METRICS
    # ============================================
    
    def record_connection_attempt(self):
        """Record a connection attempt"""
        self.reconnect_attempts += 1
        self.total_connections += 1
    
    def record_connection_established(self):
        """Record successful connection"""
        self.last_connection_time = datetime.now()
        self.connection_duration = 0
    
    def record_connection_lost(self):
        """Record connection loss"""
        if self.last_connection_time:
            self.connection_duration = (
                datetime.now() - self.last_connection_time
            ).total_seconds()
    
    # ============================================
    # ERROR METRICS
    # ============================================
    
    def record_error(self, error_type: str, message: str):
        """Record an error"""
        now = time.time()
        self.errors.append((now, error_type, message))
        self.total_errors += 1
        
        logger.error(f"[Metrics] {error_type}: {message}")
        self._cleanup_old_data()
    
    # ============================================
    # CACHE METRICS
    # ============================================
    
    def record_cache_hit(self):
        """Record a cache hit"""
        self.cache_hit_count += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        self.cache_miss_count += 1
    
    # ============================================
    # QUERY METHODS
    # ============================================
    
    def get_updates_per_second(self) -> float:
        """Get average updates per second in the window"""
        if not self.updates_received:
            return 0
        
        now = time.time()
        cutoff = now - self.window_size
        recent = [count for ts, count in self.updates_received if ts > cutoff]
        
        if not recent:
            return 0
        
        return sum(recent) / self.window_size
    
    def get_average_processing_time_ms(self) -> float:
        """Get average message processing time"""
        if not self.message_processing_times:
            return 0
        
        now = time.time()
        cutoff = now - self.window_size
        recent = [
            duration for ts, duration in self.message_processing_times if ts > cutoff
        ]
        
        if not recent:
            return 0
        
        return sum(recent) / len(recent)
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors"""
        now = time.time()
        cutoff = now - self.window_size
        recent = [
            (error_type, message, datetime.fromtimestamp(ts))
            for ts, error_type, message in self.errors
            if ts > cutoff
        ][-limit:]
        
        return recent
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.cache_hit_count + self.cache_miss_count
        if total == 0:
            return 0
        return (self.cache_hit_count / total) * 100
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        return {
            "updates": {
                "total": self.total_updates,
                "per_second": round(self.get_updates_per_second(), 2),
                "last_timestamp": datetime.fromtimestamp(
                    self.last_update_timestamp
                ).isoformat() if self.last_update_timestamp else None,
            },
            "connections": {
                "total": self.total_connections,
                "reconnect_attempts": self.reconnect_attempts,
                "last_connected": self.last_connection_time.isoformat()
                if self.last_connection_time else None,
                "last_duration_seconds": round(self.connection_duration, 2),
            },
            "errors": {
                "total": self.total_errors,
                "recent": self.get_recent_errors(5),
            },
            "performance": {
                "avg_processing_time_ms": round(
                    self.get_average_processing_time_ms(), 2
                ),
                "cache_hit_rate_percent": round(self.get_cache_hit_rate(), 2),
            },
        }
    
    # ============================================
    # MAINTENANCE
    # ============================================
    
    def _cleanup_old_data(self):
        """Remove data older than window_size"""
        now = time.time()
        cutoff = now - self.window_size
        
        # Clean updates
        while self.updates_received and self.updates_received[0][0] < cutoff:
            self.updates_received.popleft()
        
        # Clean errors
        while self.errors and self.errors[0][0] < cutoff:
            self.errors.popleft()
        
        # Clean processing times
        while self.message_processing_times and self.message_processing_times[0][0] < cutoff:
            self.message_processing_times.popleft()
    
    def reset(self):
        """Reset all metrics"""
        self.updates_received.clear()
        self.errors.clear()
        self.message_processing_times.clear()
        self.total_updates = 0
        self.total_errors = 0
        self.reconnect_attempts = 0
        self.total_connections = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        logger.info("✅ Metrics reset")


# Global metrics instance
price_stream_metrics = PriceStreamMetrics()
