"""
Advanced Rate Limiting & Throttling System
Token bucket algorithm with per-user, per-endpoint, and global limits
Phase 4: Advanced Request Management
"""

import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    REJECT = "reject"  # Reject requests when limit reached
    QUEUE = "queue"  # Queue requests and process sequentially
    DEGRADE = "degrade"  # Return degraded response (cache, etc.)
    BACKOFF = "backoff"  # Request exponential backoff


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    max_tokens: float
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    
    def __post_init__(self):
        self.tokens = self.max_tokens
        self.last_refill = time.time()
    
    def refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.max_tokens,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
    
    def consume(self, tokens: float = 1.0) -> bool:
        """Try to consume tokens"""
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_wait_time(self, tokens: float = 1.0) -> float:
        """Get seconds until tokens available"""
        self.refill()
        if self.tokens >= tokens:
            return 0.0
        shortage = tokens - self.tokens
        return shortage / self.refill_rate


@dataclass
class RateLimitStatus:
    """Status of a rate limit check"""
    allowed: bool
    remaining_tokens: float
    reset_at: datetime
    wait_seconds: float = 0


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies.
    
    Features:
    - Token bucket algorithm
    - Per-user limits
    - Per-endpoint limits
    - Global limits
    - Multiple strategies (reject, queue, degrade, backoff)
    - Quota reset tracking
    
    Example:
        limiter = RateLimiter()
        
        # Per-user limit: 100 requests per minute
        limiter.add_user_limit("user123", requests_per_minute=100)
        
        # Per-endpoint limit: 1000 requests per minute
        limiter.add_endpoint_limit("/api/prices", requests_per_minute=1000)
        
        # Check rate limit
        status = limiter.check_limit("user123", "/api/prices")
        if status.allowed:
            # Process request
        else:
            # Either queue, degrade, or backoff
    """
    
    def __init__(self):
        self.user_buckets: Dict[str, TokenBucket] = {}
        self.endpoint_buckets: Dict[str, TokenBucket] = {}
        self.global_bucket = TokenBucket(max_tokens=10000, refill_rate=166.67)  # 10k/min
        
        # Default limits
        self.default_user_limit = 100  # per minute
        self.default_endpoint_limit = 1000  # per minute
        
        self.rejected_requests = 0
        self.queued_requests = 0
        self.backoff_requests = 0
    
    def add_user_limit(self, user_id: str, requests_per_minute: int):
        """Set rate limit for a user"""
        refill_rate = requests_per_minute / 60.0
        self.user_buckets[user_id] = TokenBucket(
            max_tokens=requests_per_minute,
            refill_rate=refill_rate
        )
        logger.info(f"⚙️  User rate limit: {user_id} = {requests_per_minute}/min")
    
    def add_endpoint_limit(self, endpoint: str, requests_per_minute: int):
        """Set rate limit for an endpoint"""
        refill_rate = requests_per_minute / 60.0
        self.endpoint_buckets[endpoint] = TokenBucket(
            max_tokens=requests_per_minute,
            refill_rate=refill_rate
        )
        logger.info(f"⚙️  Endpoint rate limit: {endpoint} = {requests_per_minute}/min")
    
    def check_limit(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        cost: float = 1.0
    ) -> RateLimitStatus:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User identifier
            endpoint: API endpoint
            cost: Token cost (1 = normal request, 2+ for expensive operations)
        
        Returns:
            RateLimitStatus with allowed flag and metadata
        """
        # Get or create buckets
        user_bucket = None
        endpoint_bucket = None
        
        if user_id:
            if user_id not in self.user_buckets:
                self.add_user_limit(user_id, self.default_user_limit)
            user_bucket = self.user_buckets[user_id]
        
        if endpoint:
            if endpoint not in self.endpoint_buckets:
                self.add_endpoint_limit(endpoint, self.default_endpoint_limit)
            endpoint_bucket = self.endpoint_buckets[endpoint]
        
        # Check all limits
        allowed = True
        wait_seconds = 0.0
        
        # Global limit
        if not self.global_bucket.consume(cost):
            allowed = False
            wait_seconds = max(wait_seconds, self.global_bucket.get_wait_time(cost))
        
        # User limit
        if user_bucket and not user_bucket.consume(cost):
            allowed = False
            wait_seconds = max(wait_seconds, user_bucket.get_wait_time(cost))
        
        # Endpoint limit
        if endpoint_bucket and not endpoint_bucket.consume(cost):
            allowed = False
            wait_seconds = max(wait_seconds, endpoint_bucket.get_wait_time(cost))
        
        if not allowed:
            self.rejected_requests += 1
            logger.warning(
                f"⛔ Rate limit exceeded: user={user_id}, endpoint={endpoint}, "
                f"wait={wait_seconds:.2f}s"
            )
        
        # Get remaining tokens
        remaining = min(
            user_bucket.tokens if user_bucket else float('inf'),
            endpoint_bucket.tokens if endpoint_bucket else float('inf'),
            self.global_bucket.tokens
        )
        
        return RateLimitStatus(
            allowed=allowed,
            remaining_tokens=remaining,
            reset_at=datetime.now(timezone.utc) + timedelta(seconds=wait_seconds),
            wait_seconds=wait_seconds
        )
    
    async def handle_rate_limit(
        self,
        status: RateLimitStatus,
        strategy: RateLimitStrategy = RateLimitStrategy.REJECT,
        fallback_func=None
    ) -> Tuple[bool, Optional[str]]:
        """
        Handle rate limit based on strategy.
        
        Args:
            status: RateLimitStatus from check_limit
            strategy: How to handle the limit
            fallback_func: For DEGRADE strategy
        
        Returns:
            (should_proceed, error_message)
        """
        if status.allowed:
            return True, None
        
        if strategy == RateLimitStrategy.REJECT:
            return False, f"Rate limit exceeded. Retry after {status.wait_seconds:.1f}s"
        
        elif strategy == RateLimitStrategy.QUEUE:
            # In real implementation, would queue and process later
            self.queued_requests += 1
            logger.warning(f"📍 Queued request (wait {status.wait_seconds:.1f}s)")
            return True, "queued"  # Indicate request was queued
        
        elif strategy == RateLimitStrategy.DEGRADE:
            # Return degraded response
            if fallback_func:
                self.backoff_requests += 1
                logger.warning(f"📉 Degraded response (using fallback)")
                return True, "degraded"  # Indicate degraded response
            return False, "Rate limit exceeded"
        
        elif strategy == RateLimitStrategy.BACKOFF:
            self.backoff_requests += 1
            # Client should implement exponential backoff
            logger.warning(f"⏳ Backoff requested (wait {status.wait_seconds:.1f}s)")
            return False, f"Backoff required. Wait {status.wait_seconds:.1f}s"
        
        return False, "Rate limit exceeded"
    
    async def get_stats(self) -> Dict:
        """Get rate limiting statistics"""
        return {
            "rejected_requests": self.rejected_requests,
            "queued_requests": self.queued_requests,
            "backoff_requests": self.backoff_requests,
            "global_tokens": round(self.global_bucket.tokens, 2),
            "global_max_tokens": int(self.global_bucket.max_tokens),
            "active_user_limits": len(self.user_buckets),
            "active_endpoint_limits": len(self.endpoint_buckets),
            "global_refill_rate": f"{self.global_bucket.refill_rate:.2f} tokens/sec"
        }


# Global singleton
rate_limiter = RateLimiter()
