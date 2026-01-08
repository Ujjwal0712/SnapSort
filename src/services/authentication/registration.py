"""
Registration Service
Handles user registration logic.
"""

from psycopg_pool import AsyncConnectionPool
import asyncio
from uuid import uuid4
from typing import Tuple, Optional

from src.config.logger import logger
from src.config.settings import settings
from src.schemas.authentication import RegistrationRequest
from src.services.authentication.otp import OtpService
from src.utils.exceptions import (
    BadRequestException,
    NotFoundException,
    InternalServerException,
    DatabaseTimeoutException
)


class RegistrationService:
    """Service for user registration operations."""
    
    def __init__(self, db_pool: AsyncConnectionPool):
        """Initialize with database pool and OTP service."""
        self.db_pool = db_pool
        self.otp_service = OtpService(db_pool)
    
    async def register_user(self, request: RegistrationRequest, background_tasks=None):
        """
        Register a new user with email.
        
        Workflow:
        1. Check if email exists and account status
        2. If exists + active → Error
        3. If exists + inactive → Resend OTP
        4. If not exists → Create user + Send OTP
        """
        logger.info("Registering new user: %s", request.email)

        # Step 1: Check if email exists and get status
        try:
            async with asyncio.timeout(5):
                exists, is_active, existing_user_id = await self._check_email_exists(request.email)
        except asyncio.TimeoutError:
            logger.error("Database connection timeout")
            raise DatabaseTimeoutException()
        
        # Case 1: Email exists and account is active → Error
        if exists and is_active:
            logger.warning("Registration attempt for active account: %s", request.email)
            raise BadRequestException("Email already registered")
        
        # Case 2: Email exists but account is inactive → Resend OTP
        if exists and not is_active:
            logger.info("Resending OTP for inactive account: %s", request.email)
            try:
                async with asyncio.timeout(10):
                    await self.otp_service.send_and_store_otp(existing_user_id, request.email, background_tasks)
            except Exception as e:
                logger.error("Failed to resend OTP: %s", str(e))
                raise InternalServerException("Failed to send OTP. Please try again.")
            
            return {"message": "OTP resent to email", "user_id": existing_user_id}
        
        # Case 3: Email doesn't exist → Create new user
        user_id = None
        try:
            async with asyncio.timeout(10):
                user_id = await self._create_user(request.email)
                await self.otp_service.send_and_store_otp(user_id, request.email, background_tasks)
        except Exception as e:
            # If anything fails after user creation, cleanup the user
            if user_id:
                logger.warning("Registration failed, cleaning up user: %s", user_id)
                await self._delete_user(user_id)
            
            if isinstance(e, asyncio.TimeoutError):
                logger.error("Database connection timeout")
                raise DatabaseTimeoutException()
            else:
                logger.error("Registration failed: %s", str(e))
                raise InternalServerException("Registration failed. Please try again.")
        
        logger.info("User registered successfully: %s", request.email)
        return {"message": "User registered successfully", "user_id": user_id}
    
    async def _delete_user(self, user_id: str):
        """Delete a user (used for cleanup on failed registration)."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "DELETE FROM users WHERE id = %s",
                            (user_id,)
                        )
                    await conn.commit()
                    logger.info("Cleaned up user: %s", user_id)
        except Exception as e:
            logger.error("Failed to cleanup user %s: %s", user_id, str(e))
    
    async def _check_email_exists(self, email: str) -> Tuple[bool, bool, Optional[str]]:
        """
        Check if email already exists and get account status.
        
        Returns:
            Tuple of (exists, is_active, user_id)
        """
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        logger.info("Checking if email exists: %s", email)
                        await cur.execute(
                            "SELECT id, is_active FROM users WHERE email = %s",
                            (email,)
                        )
                        result = await cur.fetchone()
                        
                        if result is None:
                            return (False, False, None)
                        
                        user_id = str(result['id'])
                        is_active = result['is_active']
                        return (True, is_active, user_id)
        except asyncio.TimeoutError:
            logger.error("Database timeout checking email: %s", email)
            raise
        except Exception as e:
            logger.error("Database error checking email: %s - %s", email, str(e))
            raise

    async def _create_user(self, email: str) -> str:
        """
        Create a new user using a transaction.
        User is created with is_active=FALSE by default.
        
        Args:
            email: User's email address
            
        Returns:
            user_id: UUID of the created user
        """
        logger.info("Creating new user: %s", email)
        user_id = str(uuid4())
        
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.transaction():
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """
                                INSERT INTO users (id, email, is_active)
                                VALUES (%s, %s, FALSE)
                                """,
                                (user_id, email)
                            )
                    
                    logger.info("User created with id: %s", user_id)
                    return user_id
                    
        except asyncio.TimeoutError:
            logger.error("Database timeout creating user: %s", email)
            raise
        except Exception as e:
            logger.error("Database error creating user: %s - %s", email, str(e))
            raise

    async def complete_registration(self, user_id: str, username: str, password: str, selfie_url: str, file_id: str) -> dict:
        """
        Complete user registration with username, password, and selfie.
        
        Args:
            user_id: User's UUID (from registration token)
            username: User's chosen username
            password: User's password (will be hashed)
            selfie_url: URL to user's uploaded selfie
            file_id: ImageKit file ID for the selfie image (for deletion)
            
        Returns:
            Success message with user_id
            
        Raises:
            ServiceException: If user not found, username taken, or DB error
        """
        logger.info("Completing registration for user: %s", user_id)
        
        # Check if username is already taken
        try:
            async with asyncio.timeout(5):
                username_exists = await self._check_username_exists(username)
                if username_exists:
                    raise BadRequestException("Username already taken")
        except asyncio.TimeoutError:
            logger.error("Database timeout checking username")
            raise DatabaseTimeoutException()
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Update user and create credentials
        try:
            async with asyncio.timeout(10):
                async with self.db_pool.connection() as conn:
                    async with conn.transaction():
                        async with conn.cursor() as cur:
                            # Update user with username, selfie_url, file_id and activate
                            await cur.execute(
                                """
                                UPDATE users 
                                SET username = %s, selfie_url = %s, file_id = %s, is_active = TRUE, updated_at = NOW()
                                WHERE id = %s AND is_active = FALSE
                                RETURNING id
                                """,
                                (username, selfie_url, file_id, user_id)
                            )
                            result = await cur.fetchone()
                            
                            if not result:
                                raise NotFoundException("User not found or already activated")
                            
                            # Insert credentials
                            await cur.execute(
                                """
                                INSERT INTO user_credentials (user_id, password_hash)
                                VALUES (%s, %s)
                                ON CONFLICT (user_id) DO UPDATE SET
                                    password_hash = EXCLUDED.password_hash,
                                    updated_at = NOW()
                                """,
                                (user_id, password_hash)
                            )
                    
                    logger.info("Registration completed for user: %s", user_id)
                    return {"message": "Registration completed successfully"}
                    
        except (BadRequestException, NotFoundException):
            raise
        except asyncio.TimeoutError:
            logger.error("Database timeout completing registration")
            raise DatabaseTimeoutException()
        except Exception as e:
            logger.error("Error completing registration: %s", str(e))
            raise InternalServerException("Failed to complete registration")

    async def _check_username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT 1 FROM users WHERE username = %s",
                    (username,)
                )
                return await cur.fetchone() is not None

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt via passlib."""
        from passlib.hash import bcrypt
        return bcrypt.hash(password)
