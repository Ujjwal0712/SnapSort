"""
Authentication Dependencies
FastAPI dependencies for access token validation and user context.
"""

from typing import Optional
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status, Header

from src.utils.token import verify_access_token


@dataclass
class CurrentUser:
    """User context from validated access token."""
    user_id: str
    username: str
    session_id: str


async def get_current_user(
    authorization: str = Header(..., description="Bearer access token")
) -> CurrentUser:
    """
    Dependency to validate access token and return current user context.
    
    Usage:
        @router.get("/protected")
        async def protected_route(current_user: CurrentUser = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        CurrentUser with user_id, username, and session_id
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # Verify the access token (raises HTTPException if invalid)
    payload = verify_access_token(token)
    
    return CurrentUser(
        user_id=payload.get("sub"),
        username=payload.get("username"),
        session_id=payload.get("session_id")
    )


async def get_optional_user(
    authorization: Optional[str] = Header(None, description="Bearer access token")
) -> Optional[CurrentUser]:
    """
    Optional dependency - returns None if no token provided.
    
    Useful for routes that work for both authenticated and anonymous users.
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
