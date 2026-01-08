"""
Login Service
Handles user authentication with email/username and password.
"""

import asyncio
from uuid import uuid4
from typing import Optional
from psycopg_pool import AsyncConnectionPool

from src.config.logger import logger
from src.config.settings import settings
from src.schemas.authentication import LoginRequest
from src.utils.token import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    get_refresh_token_expiry
)
from src.utils.exceptions import (
    UnauthorizedException,
    DatabaseTimeoutException
)


class LoginService:
    """Service for user login and session management."""
    
    def __init__(self, db_pool: AsyncConnectionPool):
        self.db_pool = db_pool
    
    async def login(self, request: LoginRequest) -> dict:
        """
        Authenticate user with email/username and password.
        
        Args:
            request: LoginRequest with identifier, password, device_info, ip_address
            
        Returns:
            Dict with user info and tokens
            
        Raises:
            UnauthorizedException: If credentials invalid or user not found
        """
        logger.info("Login attempt for: %s", request.identifier)
        
        # Find user by email or username
        user = await self._find_user_by_identifier(request.identifier)
        
        if not user:
            logger.warning("Login failed - user not found: %s", request.identifier)
            raise UnauthorizedException("Invalid credentials")
        
        user_id = str(user['id'])
        username = user['username']
        is_active = user['is_active']
        
        # Check if account is active
        if not is_active:
            logger.warning("Login failed - account not active: %s", request.identifier)
            raise UnauthorizedException("Account not activated")
        
        # Verify password
        password_valid = await self._verify_password(user_id, request.password)
        
        if not password_valid:
            logger.warning("Login failed - invalid password: %s", request.identifier)
            raise UnauthorizedException("Invalid credentials")
        
        # Generate refresh token first
        refresh_token = create_refresh_token()
        refresh_token_hash = hash_refresh_token(refresh_token)
        
        # Create session and get session_id
        session_id = await self._create_session(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            device_info=request.device_info,
            ip_address=request.ip_address
        )
        
        # Generate access token with session_id
        access_token = create_access_token(user_id, username, session_id)
        
        logger.info("Login successful for user: %s", username)
        
        return {
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    
    async def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Refresh access token using a valid refresh token.
        
        Args:
            refresh_token: The refresh token to validate
            
        Returns:
            New access token
            
        Raises:
            UnauthorizedException: If refresh token invalid or expired
        """
        refresh_token_hash = hash_refresh_token(refresh_token)
        
        # Find session by refresh token hash
        session = await self._find_session_by_token_hash(refresh_token_hash)
        
        if not session:
            raise UnauthorizedException("Invalid refresh token")
        
        user_id = str(session['user_id'])
        session_id = str(session['id'])
        
        # Get user info for new access token
        user = await self._get_user_by_id(user_id)
        
        if not user or not user['is_active']:
            raise UnauthorizedException("User account not active")
        
        # Generate new access token with session_id
        access_token = create_access_token(user_id, user['username'], session_id)
        
        return {
            "access_token": access_token,
        }
    
    async def logout(self, session_id: str) -> dict:
        """
        Logout user by invalidating the current session.
        
        Args:
            session_id: Session UUID from access token
            
        Returns:
            Success message
        """
        await self._delete_session_by_id(session_id)
        
        return {"message": "Logged out successfully"}
    
    async def _delete_session_by_id(self, session_id: str):
        """Delete session by session ID."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "DELETE FROM user_sessions WHERE id = %s",
                            (session_id,)
                        )
                    await conn.commit()
                    logger.info("Session deleted: %s", session_id)
        except asyncio.TimeoutError:
            logger.error("Database timeout deleting session")
    
    async def _find_user_by_identifier(self, identifier: str) -> Optional[dict]:
        """Find user by email or username."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            SELECT id, username, email, is_active 
                            FROM users 
                            WHERE email = %s OR username = %s
                            """,
                            (identifier, identifier)
                        )
                        return await cur.fetchone()
        except asyncio.TimeoutError:
            logger.error("Database timeout finding user: %s", identifier)
            raise DatabaseTimeoutException()
    
    async def _verify_password(self, user_id: str, password: str) -> bool:
        """Verify password against stored hash."""
        from passlib.hash import bcrypt
        
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "SELECT password_hash FROM user_credentials WHERE user_id = %s",
                            (user_id,)
                        )
                        result = await cur.fetchone()
                        
                        if not result:
                            return False
                        
                        return bcrypt.verify(password, result['password_hash'])
        except asyncio.TimeoutError:
            logger.error("Database timeout verifying password")
            raise DatabaseTimeoutException()
    
    async def _create_session(
        self, 
        user_id: str, 
        refresh_token_hash: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Create a new user session and return session_id."""
        session_id = str(uuid4())
        expires_at = get_refresh_token_expiry()
        
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            INSERT INTO user_sessions (id, user_id, refresh_token_hash, device_info, ip_address, expires_at)
                            VALUES (%s, %s, %s, %s, %s::inet, %s)
                            """,
                            (session_id, user_id, refresh_token_hash, device_info, ip_address, expires_at)
                        )
                    await conn.commit()
                    logger.info("Session created for user: %s with id: %s", user_id, session_id)
                    return session_id
        except asyncio.TimeoutError:
            logger.error("Database timeout creating session")
            raise DatabaseTimeoutException()
    
    async def _find_session_by_token_hash(self, refresh_token_hash: str) -> Optional[dict]:
        """Find session by refresh token hash."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            SELECT id, user_id, expires_at 
                            FROM user_sessions 
                            WHERE refresh_token_hash = %s AND expires_at > now()
                            """,
                            (refresh_token_hash,)
                        )
                        return await cur.fetchone()
        except asyncio.TimeoutError:
            logger.error("Database timeout finding session")
            raise DatabaseTimeoutException()
    
    async def _get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "SELECT id, username, is_active FROM users WHERE id = %s",
                            (user_id,)
                        )
                        return await cur.fetchone()
        except asyncio.TimeoutError:
            logger.error("Database timeout getting user")
            raise DatabaseTimeoutException()
    