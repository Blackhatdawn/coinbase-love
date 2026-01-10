from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth import decode_token
from typing import Optional

security = HTTPBearer(auto_error=False)


async def get_current_user_id(request: Request) -> str:
    """Extract user ID from JWT token in cookie or Authorization header"""
    
    # First try to get token from cookie
    token = request.cookies.get("access_token")
    
    # If not in cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Decode token
    payload = decode_token(token)
    if not payload:
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
    """Extract user ID from JWT token, return None if not authenticated"""
    try:
        return await get_current_user_id(request)
    except HTTPException:
        return None
