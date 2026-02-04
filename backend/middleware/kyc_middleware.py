"""
KYC Middleware - Enforce compliance restrictions
Blocks unapproved users from sensitive financial operations
"""
import logging
from typing import Callable
from fastapi import Request, HTTPException, status
from functools import wraps

logger = logging.getLogger(__name__)


class KYCRequiredException(HTTPException):
    """Exception raised when KYC verification is required"""
    def __init__(self, detail: str = "KYC verification required"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_user_from_request(request: Request) -> dict:
    """Extract user from request state (set by auth middleware)"""
    if hasattr(request.state, 'user'):
        return request.state.user
    return None


def require_kyc_approved(func: Callable):
    """
    Decorator to require KYC approval for sensitive operations.
    
    Usage:
        @router.post("/deposit")
        @require_kyc_approved
        async def create_deposit(request: Request):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            # Try to get from kwargs
            request = kwargs.get('request')
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        # Get user from request state
        user = await get_user_from_request(request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check KYC status
        kyc_status = user.get('kyc_status', 'pending')
        
        if kyc_status != 'approved':
            logger.warning(f"KYC check failed for user {user['id']}: status={kyc_status}")
            
            if kyc_status == 'pending':
                raise KYCRequiredException(
                    detail="Your KYC verification is pending. Please wait for admin approval."
                )
            elif kyc_status == 'rejected':
                rejection_reason = user.get('kyc_rejection_reason', 'KYC verification failed')
                raise KYCRequiredException(
                    detail=f"Your KYC was rejected: {rejection_reason}. Please resubmit with correct documents."
                )
            else:
                raise KYCRequiredException(
                    detail="KYC verification required to perform this action."
                )
        
        # KYC approved - proceed
        return await func(*args, **kwargs)
    
    return wrapper


def require_kyc_tier(min_tier: int):
    """
    Decorator to require minimum KYC tier for operations.
    
    Tier Levels:
    - Tier 0: Unverified ($500/day limit)
    - Tier 1: Basic KYC ($5,000/day limit)
    - Tier 2: Advanced KYC ($50,000/day limit)
    
    Usage:
        @router.post("/withdraw")
        @require_kyc_tier(1)
        async def create_withdrawal(request: Request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Get user from request state
            user = await get_user_from_request(request)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check KYC tier
            current_tier = user.get('kyc_tier', 0)
            
            if current_tier < min_tier:
                logger.warning(f"KYC tier check failed for user {user['id']}: current={current_tier}, required={min_tier}")
                
                tier_limits = {
                    0: "$500/day",
                    1: "$5,000/day",
                    2: "$50,000/day"
                }
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This operation requires KYC Tier {min_tier}+. Your current tier: {current_tier} ({tier_limits.get(current_tier, 'Unknown')} limit)"
                )
            
            # Tier requirement met - proceed
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def check_daily_limit(user_id: str, amount: float, operation: str, db) -> bool:
    """
    Check if user's transaction exceeds their daily limit based on KYC tier.
    
    Returns: True if within limits, raises exception if exceeded
    """
    from datetime import datetime, timezone, timedelta
    
    # Get user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    kyc_tier = user.get('kyc_tier', 0)
    
    # Define daily limits by tier
    tier_limits = {
        0: 500.0,      # $500/day for unverified
        1: 5000.0,     # $5,000/day for basic KYC
        2: 50000.0,    # $50,000/day for advanced KYC
        3: 500000.0    # $500,000/day for premium (future)
    }
    
    daily_limit = tier_limits.get(kyc_tier, 500.0)
    
    # Calculate 24-hour period
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    
    # Get today's transactions (deposits + withdrawals)
    transactions = []
    
    # Check deposits
    deposits = await db.deposits.find({
        "user_id": user_id,
        "created_at": {"$gte": yesterday},
        "status": {"$in": ["completed", "pending"]}
    }).to_list(length=None)
    transactions.extend([d.get('amount', 0) for d in deposits])
    
    # Check withdrawals
    withdrawals = await db.withdrawals.find({
        "user_id": user_id,
        "created_at": {"$gte": yesterday},
        "status": {"$in": ["completed", "pending"]}
    }).to_list(length=None)
    transactions.extend([w.get('amount', 0) for w in withdrawals])
    
    # Calculate total
    total_today = sum(transactions) + amount
    
    if total_today > daily_limit:
        logger.warning(f"Daily limit exceeded for user {user_id}: ${total_today:.2f} > ${daily_limit:.2f}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Daily limit exceeded. Your KYC Tier {kyc_tier} limit is ${daily_limit:,.2f}/day. Current usage: ${total_today - amount:,.2f}. Upgrade your KYC tier for higher limits."
        )
    
    return True


def get_kyc_restrictions(kyc_status: str, kyc_tier: int) -> dict:
    """
    Get user's restrictions based on KYC status and tier.
    
    Returns dict with allowed operations and limits.
    """
    if kyc_status == 'approved':
        tier_limits = {
            0: {"daily_limit": 500, "can_trade": True, "can_withdraw": True},
            1: {"daily_limit": 5000, "can_trade": True, "can_withdraw": True},
            2: {"daily_limit": 50000, "can_trade": True, "can_withdraw": True}
        }
        return tier_limits.get(kyc_tier, tier_limits[0])
    
    elif kyc_status == 'pending':
        # Pending users: read-only access
        return {
            "daily_limit": 0,
            "can_trade": False,
            "can_withdraw": False,
            "can_deposit": False,
            "message": "KYC verification pending. Limited access until approved."
        }
    
    else:  # rejected or not started
        return {
            "daily_limit": 0,
            "can_trade": False,
            "can_withdraw": False,
            "can_deposit": False,
            "message": "KYC verification required. Please submit your documents."
        }
