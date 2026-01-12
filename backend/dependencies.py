from fastapi import Request, HTTPException, status
from auth import decode_token
from blacklist import is_token_blacklisted  # New import
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def get_current_user_id(request: Request) -> str:
    """Extract and validate user ID from JWT access token (cookie or header)."""
   
    # Get token from cookie or Authorization header
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
   
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
   
    # NEW: Check blacklist
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked (logged out)"
        )
   
    # Decode token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
   
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
   
    return user_id

async def optional_current_user_id(request: Request) -> Optional[str]:
    """Optional version – returns None if not authenticated."""
    try:
        return await get_current_user_id(request)
    except HTTPException:
        return None
