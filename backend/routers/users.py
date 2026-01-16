"""User management endpoints."""

from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime
from typing import Optional, List
import logging

from dependencies import get_current_user_id, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


# ============================================
# USER SEARCH ENDPOINTS
# ============================================

@router.get("/search")
async def search_users(
    email: str = Query(..., min_length=1, description="Email to search for (case-insensitive)"),
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """
    Search for users by email (public search, non-sensitive).
    
    Returns a list of users matching the email search query.
    This endpoint is used for P2P transfers to find recipients.
    
    **Query Parameters:**
    - `email`: Email search term (required, case-insensitive)
    
    **Response:**
    ```json
    {
        "users": [
            {
                "id": "uuid",
                "email": "user@example.com",
                "name": "John Doe"
            }
        ]
    }
    ```
    
    **Status Codes:**
    - 200: Success
    - 401: Unauthorized
    - 400: Invalid query
    - 500: Server error
    """
    users_collection = db.get_collection("users")

    # Limit search results to prevent abuse
    max_results = 10

    try:
        # Search for users by email (case-insensitive regex)
        # Exclude the current user from results
        users = await users_collection.find({
            "email": {"$regex": email, "$options": "i"},
            "id": {"$ne": current_user_id},
            "email_verified": True  # Only show verified users
        }).to_list(max_results)

        # Format response (don't expose sensitive data)
        formatted_users = [
            {
                "id": user.get("id"),
                "email": user.get("email"),
                "name": user.get("name", "")
            }
            for user in users
        ]

        logger.info(
            f"User search completed",
            extra={
                "type": "user_search",
                "user_id": current_user_id,
                "search_term": email,
                "results": len(formatted_users)
            }
        )

        return {
            "users": formatted_users,
            "count": len(formatted_users)
        }

    except Exception as e:
        logger.error(
            f"User search failed: {str(e)}",
            extra={"type": "user_search_error", "user_id": current_user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Search failed. Please try again."
        )


@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """
    Get public user profile information.
    
    Returns non-sensitive user information.
    Users can only view other users' public profiles.
    
    **Path Parameters:**
    - `user_id`: UUID of the user to fetch
    
    **Response:**
    ```json
    {
        "id": "uuid",
        "email": "user@example.com",
        "name": "John Doe",
        "created_at": "2026-01-16T12:00:00"
    }
    ```
    
    **Status Codes:**
    - 200: Success
    - 401: Unauthorized
    - 404: User not found
    - 500: Server error
    """
    users_collection = db.get_collection("users")

    try:
        user = await users_collection.find_one(
            {
                "id": user_id,
                "email_verified": True  # Only return verified users
            }
        )

        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Return only public profile data
        return {
            "id": user.get("id"),
            "email": user.get("email"),
            "name": user.get("name", ""),
            "created_at": user.get("created_at", datetime.utcnow()).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Get user profile failed: {str(e)}",
            extra={"type": "get_user_error", "user_id": user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user profile"
        )
