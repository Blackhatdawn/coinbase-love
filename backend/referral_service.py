"""
Referral System Service
Handles referral codes, tracking, and rewards
"""
import os
import random
import string
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from bson import ObjectId

logger = logging.getLogger(__name__)


class ReferralService:
    """Referral program management"""
    
    # Reward configuration
    REFERRER_REWARD_PERCENT = 10.0  # 10% of referee's trading fees
    REFEREE_BONUS = 10.0  # $10 bonus for referee after first trade
    MIN_TRADE_VOLUME = 100.0  # Minimum trade volume to qualify
    REWARD_DURATION_MONTHS = 3  # Lifetime or limited months
    
    def __init__(self, db):
        self.db = db
    
    def generate_referral_code(self, length: int = 8) -> str:
        """Generate unique referral code"""
        chars = string.ascii_uppercase + string.digits
        # Remove confusing characters
        chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        return ''.join(random.choices(chars, k=length))
    
    async def get_or_create_referral_code(self, user_id: str) -> str:
        """Get existing or create new referral code for user"""
        users_col = self.db.get_collection("users")
        
        user = await users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")
        
        # Check if user already has a code
        existing_code = user.get("referral_code")
        if existing_code:
            return existing_code
        
        # Generate new unique code
        for _ in range(10):  # Max 10 attempts
            code = self.generate_referral_code()
            # Check uniqueness
            existing = await users_col.find_one({"referral_code": code})
            if not existing:
                # Save to user
                await users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"referral_code": code, "referral_code_created_at": datetime.utcnow()}}
                )
                return code
        
        raise Exception("Failed to generate unique referral code")
    
    async def apply_referral_code(self, referee_id: str, referral_code: str) -> Dict[str, Any]:
        """
        Apply referral code when new user signs up
        
        Args:
            referee_id: ID of the new user being referred
            referral_code: Referral code from the referrer
        """
        users_col = self.db.get_collection("users")
        referrals_col = self.db.get_collection("referrals")
        
        # Find referrer by code
        referrer = await users_col.find_one({"referral_code": referral_code})
        if not referrer:
            return {"success": False, "error": "Invalid referral code"}
        
        referrer_id = str(referrer["_id"])
        
        # Prevent self-referral
        if referrer_id == referee_id:
            return {"success": False, "error": "Cannot use your own referral code"}
        
        # Check if referee was already referred
        existing = await referrals_col.find_one({"referee_id": referee_id})
        if existing:
            return {"success": False, "error": "User already has a referrer"}
        
        # Create referral record
        referral_doc = {
            "referrer_id": referrer_id,
            "referee_id": referee_id,
            "referral_code": referral_code,
            "status": "pending",  # pending, qualified, expired
            "referee_trade_volume": 0,
            "rewards_paid": 0,
            "created_at": datetime.utcnow(),
            "qualified_at": None,
            "expires_at": datetime.utcnow() + timedelta(days=90)  # 90 days to qualify
        }
        
        await referrals_col.insert_one(referral_doc)
        
        # Update referrer's stats
        await users_col.update_one(
            {"_id": ObjectId(referrer_id)},
            {
                "$inc": {"total_referrals": 1},
                "$push": {"referral_ids": referee_id}
            }
        )
        
        # Update referee's record
        await users_col.update_one(
            {"_id": ObjectId(referee_id)},
            {"$set": {"referred_by": referrer_id, "referral_code_used": referral_code}}
        )
        
        logger.info(f"✅ Referral applied: {referee_id} referred by {referrer_id}")
        
        return {
            "success": True,
            "referrer_name": referrer.get("name", "A friend"),
            "message": f"Referral code applied! Trade ${self.MIN_TRADE_VOLUME}+ to unlock your bonus."
        }
    
    async def process_trade_for_referral(
        self, 
        user_id: str, 
        trade_volume: float,
        trading_fee: float
    ) -> Optional[Dict[str, Any]]:
        """
        Process a trade and update referral rewards if applicable
        
        Args:
            user_id: ID of the user who made the trade
            trade_volume: Total trade volume in USD
            trading_fee: Trading fee paid in USD
        """
        referrals_col = self.db.get_collection("referrals")
        users_col = self.db.get_collection("users")
        rewards_col = self.db.get_collection("referral_rewards")
        
        # Find referral record where this user is the referee
        referral = await referrals_col.find_one({
            "referee_id": user_id,
            "status": {"$in": ["pending", "qualified"]}
        })
        
        if not referral:
            return None
        
        referrer_id = referral["referrer_id"]
        current_volume = referral.get("referee_trade_volume", 0)
        new_volume = current_volume + trade_volume
        
        # Check if within reward period (if limited)
        created_at = referral.get("created_at")
        if self.REWARD_DURATION_MONTHS > 0 and created_at:
            cutoff = created_at + timedelta(days=30 * self.REWARD_DURATION_MONTHS)
            if datetime.utcnow() > cutoff:
                await referrals_col.update_one(
                    {"_id": referral["_id"]},
                    {"$set": {"status": "expired"}}
                )
                return None
        
        # Calculate referrer reward
        referrer_reward = trading_fee * (self.REFERRER_REWARD_PERCENT / 100)
        
        updates = {
            "referee_trade_volume": new_volume,
            "rewards_paid": referral.get("rewards_paid", 0) + referrer_reward
        }
        
        result = {
            "referrer_reward": referrer_reward,
            "referee_bonus": 0
        }
        
        # Check if referee just qualified
        if referral["status"] == "pending" and new_volume >= self.MIN_TRADE_VOLUME:
            updates["status"] = "qualified"
            updates["qualified_at"] = datetime.utcnow()
            result["referee_bonus"] = self.REFEREE_BONUS
            
            # Credit referee bonus
            await users_col.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"balance": self.REFEREE_BONUS}}
            )
            
            logger.info(f"🎉 Referee {user_id} qualified! Bonus: ${self.REFEREE_BONUS}")
        
        # Update referral record
        await referrals_col.update_one(
            {"_id": referral["_id"]},
            {"$set": updates}
        )
        
        # Credit referrer reward
        await users_col.update_one(
            {"_id": ObjectId(referrer_id)},
            {"$inc": {"referral_earnings": referrer_reward, "balance": referrer_reward}}
        )
        
        # Log reward transaction
        await rewards_col.insert_one({
            "referrer_id": referrer_id,
            "referee_id": user_id,
            "trade_volume": trade_volume,
            "trading_fee": trading_fee,
            "reward_amount": referrer_reward,
            "created_at": datetime.utcnow()
        })
        
        if referrer_reward > 0:
            logger.info(f"💰 Referral reward: ${referrer_reward:.2f} to {referrer_id}")
        
        return result
    
    async def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """Get referral statistics for a user"""
        users_col = self.db.get_collection("users")
        referrals_col = self.db.get_collection("referrals")
        
        user = await users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"error": "User not found"}
        
        # Get referral code
        referral_code = await self.get_or_create_referral_code(user_id)
        
        # Count referrals by status
        total_referrals = await referrals_col.count_documents({"referrer_id": user_id})
        qualified_referrals = await referrals_col.count_documents({
            "referrer_id": user_id,
            "status": "qualified"
        })
        pending_referrals = await referrals_col.count_documents({
            "referrer_id": user_id,
            "status": "pending"
        })
        
        # Calculate total earnings
        total_earnings = user.get("referral_earnings", 0)
        
        # Get recent referrals
        recent_cursor = referrals_col.find(
            {"referrer_id": user_id}
        ).sort("created_at", -1).limit(10)
        
        recent_referrals = []
        async for ref in recent_cursor:
            referee = await users_col.find_one({"_id": ObjectId(ref["referee_id"])})
            recent_referrals.append({
                "referee_name": referee.get("name", "Anonymous")[:2] + "***" if referee else "Unknown",
                "status": ref["status"],
                "trade_volume": ref.get("referee_trade_volume", 0),
                "created_at": ref["created_at"].isoformat()
            })
        
        return {
            "referral_code": referral_code,
            "referral_link": f"https://cryptovault.financial/auth?ref={referral_code}",
            "total_referrals": total_referrals,
            "qualified_referrals": qualified_referrals,
            "pending_referrals": pending_referrals,
            "total_earnings": total_earnings,
            "reward_rate": f"{self.REFERRER_REWARD_PERCENT}%",
            "min_trade_volume": self.MIN_TRADE_VOLUME,
            "recent_referrals": recent_referrals
        }
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top referrers leaderboard"""
        users_col = self.db.get_collection("users")
        
        cursor = users_col.find(
            {"referral_earnings": {"$gt": 0}},
            {"name": 1, "referral_earnings": 1, "total_referrals": 1}
        ).sort("referral_earnings", -1).limit(limit)
        
        leaderboard = []
        rank = 1
        async for user in cursor:
            # Mask name for privacy
            name = user.get("name", "Anonymous")
            masked_name = name[0] + "*" * (len(name) - 2) + name[-1] if len(name) > 2 else name
            
            leaderboard.append({
                "rank": rank,
                "name": masked_name,
                "referrals": user.get("total_referrals", 0),
                "earnings": user.get("referral_earnings", 0)
            })
            rank += 1
        
        return leaderboard
