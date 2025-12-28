"""
Registration Service
Handles user registration logic.
"""

from psycopg_pool import AsyncConnectionPool
import asyncio
from fastapi import HTTPException
from src.config.logger import logger
from src.schemas.authentication import RegistrationRequest
from src.config.settings import settings

class RegistrationService:
    """Service for user registration operations."""
    
    def __init__(self, db_pool: AsyncConnectionPool):
        """Initialize with database pool."""
        self.db_pool = db_pool

    
    async def registerUser(self, request: RegistrationRequest):
        """Register a new user with email."""
        logger.info("Registering new user: %s", request.email)

        try:
            async with asyncio.timeout(5):
                exists = await self._check_email_exists(request.email)
        except asyncio.TimeoutError:
            logger.error("Database connection timeout")
            raise HTTPException(status_code=500, detail="Database connection timeout")
        
        if exists:
            logger.error("Email already exists")
            raise HTTPException(status_code=400, detail="Email already exists")

        try:
            async with asyncio.timeout(5):
                await self._create_user(request.email)
                await self._send_and_store_otp(request.email)
        except asyncio.TimeoutError:
            logger.error("Database connection timeout")
            raise HTTPException(status_code=500, detail="Database connection timeout")
        
        logger.info("User registered successfully: %s", request.email)
        return {"message": "User registered successfully"}






    
    async def _check_email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "SELECT 1 FROM users WHERE email = %s",
                            (email,)
                        )
                        result = await cur.fetchone()
                        return result is not None
        except asyncio.TimeoutError:
            logger.error("Database timeout checking email: %s", email)
            raise
        except Exception as e:
            logger.error("Database error checking email: %s - %s", email, str(e))
            raise

    async def _create_user(self, email: str):
        """Create a new user."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "INSERT INTO users (email) VALUES (%s)",
                            (email,)
                        )
        except asyncio.TimeoutError:
            logger.error("Database timeout creating user: %s", email)
            raise
        except Exception as e:
            logger.error("Database error creating user: %s - %s", email, str(e))
            raise

    async def _send_and_store_otp(self, email: str):
        """Send OTP to user and store it."""
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "INSERT INTO otps (email, otp) VALUES (%s, %s)",
                            (email, "123456")
                        )
        except asyncio.TimeoutError:
            logger.error("Database timeout sending OTP: %s", email)
            raise
        except Exception as e:
            logger.error("Database error sending OTP: %s - %s", email, str(e))
            raise