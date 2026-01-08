"""
Token Utilities
JWT token generation and verification for authentication flows.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status

from src.config.settings import settings


def create_registration_token(user_id: str) -> str:
    """
    Create a short-lived JWT token for completing registration.
    
    This token authorizes the user to proceed with the next registration steps
    (selfie upload, username, password) after successful OTP verification.
    
    Args:
        user_id: The user's UUID as a string
        
    Returns:
        JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REGISTRATION_TOKEN_EXPIRE_MINUTES
    )
    
    payload = {
        "sub": user_id,
        "type": "registration",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


def verify_registration_token(token: str) -> dict:
    """
    Verify a registration token and return its payload.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload dict with 'sub' (user_id) and 'type'
        
    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify this is a registration token
        if payload.get("type") != "registration":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired registration token"
        )


def create_access_token(user_id: str, username: str, session_id: str) -> str:
    """
    Create a short-lived JWT access token for API authentication.
    
    Args:
        user_id: User's UUID
        username: User's username
        session_id: Session UUID for this login session
        
    Returns:
        JWT access token string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    payload = {
        "sub": user_id,
        "username": username,
        "session_id": session_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token() -> str:
    """
    Create a cryptographically secure refresh token.
    
    Returns:
        Random token string (64 characters)
    """
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token for secure storage.
    
    Args:
        token: Plain refresh token
        
    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_access_token(token: str) -> dict:
    """
    Verify an access token and return its payload.
    
    Args:
        token: JWT access token string
        
    Returns:
        Token payload dict with 'sub' (user_id), 'username', 'type'
        
    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )


def get_refresh_token_expiry() -> datetime:
    """Get the expiry datetime for a new refresh token."""
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
