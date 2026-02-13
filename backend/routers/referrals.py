"""Referral endpoints for dashboard integrations."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.get("/summary")
async def get_referral_summary(user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    users = db.get_collection("users")
    referrals = db.get_collection("referrals")

    user = await users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    referral_code = user.get("referral_code") or f"CV{user_id[-6:].upper()}"
    app_url = "https://www.cryptovault.financial"

    total_referrals = await referrals.count_documents({"referrer_id": user_id})
    active_referrals = await referrals.count_documents({"referrer_id": user_id, "status": "qualified"})
    pending_referrals = await referrals.count_documents({"referrer_id": user_id, "status": "pending"})

    return {
        "referralCode": referral_code,
        "referralLink": f"{app_url}/auth?ref={referral_code}",
        "totalReferrals": total_referrals,
        "activeReferrals": active_referrals,
        "pendingReferrals": pending_referrals,
        "totalEarned": float(user.get("referral_earnings", 0.0)),
        "commissionRate": 10,
    }


@router.get("")
async def list_referrals(user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    users = db.get_collection("users")
    referrals = db.get_collection("referrals")

    cursor = referrals.find({"referrer_id": user_id}).sort("created_at", -1).limit(100)
    items = []
    async for ref in cursor:
        referee = await users.find_one({"id": ref.get("referee_id")})
        email = referee.get("email") if referee else "hidden@example.com"
        masked_email = (email[:1] + "***@" + email.split("@")[-1]) if "@" in email else "hidden@example.com"
        items.append({
            "id": ref.get("id") or str(ref.get("_id")),
            "email": masked_email,
            "status": ref.get("status", "pending"),
            "earned": round(float(ref.get("rewards_paid", 0.0)), 2),
            "date": (ref.get("created_at") or datetime.utcnow()).date().isoformat(),
        })

    return {"referrals": items}
