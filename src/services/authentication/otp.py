"""
OTP Service
Handles OTP generation, sending via email, and storage.
"""

import secrets
import hashlib
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from datetime import timezone

from psycopg_pool import AsyncConnectionPool
from mailersend import MailerSendClient, EmailBuilder

from src.config.settings import settings
from src.config.logger import logger


class OtpService:
    """Service for OTP operations."""
    
    def __init__(self, db_pool: AsyncConnectionPool):
        """Initialize with database pool."""
        self.db_pool = db_pool
        self.email_client = MailerSendClient(api_key=settings.MAILERSEND_API_KEY)
    
    def _generate_otp(self) -> str:
        """
        Generate a cryptographically secure random numeric OTP.
        Uses secrets.randbelow for crypto-secure randomness with zero-padding.
        """
        length = settings.OTP_LENGTH
        if length <= 0:
            raise ValueError("Invalid OTP length")
        
        # Generate cryptographically secure random number between 0 and 10^length
        max_value = 10 ** length
        n = secrets.randbelow(max_value)
        
        # Format with leading zeros to maintain consistent length
        otp = str(n).zfill(length)
        return otp
    
    def _hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    async def send_and_store_otp(self, user_id: str, email: str, background_tasks=None) -> bool:
        """
        Generate OTP, store hash in database, and send via email.
        
        Args:
            user_id: User's UUID
            email: User's email address
            background_tasks: Optional FastAPI BackgroundTasks for async email
            
        Returns:
            True if OTP stored successfully, raises exception otherwise
        """
        # Generate OTP
        otp = self._generate_otp()
        otp_hash = self._hash_otp(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        
        logger.info("Generating OTP for: %s", email)
        
        try:
            # Store OTP in database first (this is fast)
            async with asyncio.timeout(5):
                await self._store_otp(user_id, otp_hash, expires_at)
            
            # Send email in background if background_tasks provided
            if background_tasks:
                background_tasks.add_task(self._send_otp_email_sync, email, otp)
                logger.info("OTP stored, email queued for: %s", email)
            else:
                # Fallback to synchronous sending
                self._send_otp_email_sync(email, otp)
                logger.info("OTP sent successfully to: %s", email)
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout storing OTP for: %s", email)
            raise
        except Exception as e:
            logger.error("Error sending OTP to %s: %s", email, str(e))
            raise
    
    def _send_otp_email_sync(self, email: str, otp: str):
        """Send OTP via email using MailerSend (synchronous for background task)."""
        try:
            email_message = (
                EmailBuilder()
                .from_email(settings.MAILERSEND_FROM_EMAIL, "SnapSort")
                .to_many([{"email": email}])
                .subject("Your SnapSort Verification Code")
                .html(f"""
                    <h2>Your Verification Code</h2>
                    <p>Use the following code to verify your email:</p>
                    <h1 style="font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                    <p>This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                """)
                .text(f"Your SnapSort verification code is: {otp}. Expires in {settings.OTP_EXPIRY_MINUTES} minutes.")
                .build()
            )
            
            self.email_client.emails.send(email_message)
            logger.info("Email sent successfully to: %s", email)
        except Exception as e:
            logger.error("Failed to send email to %s: %s", email, str(e))
    
    async def _store_otp(self, user_id: str, otp_hash: str, expires_at: datetime):
        """Store OTP hash in database."""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cur:
                # Upsert - update if exists, insert if not
                await cur.execute(
                    """
                    INSERT INTO user_otps (user_id, email_otp_hash, expires_at, attempts)
                    VALUES (%s, %s, %s, 0)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_otp_hash = EXCLUDED.email_otp_hash,
                        expires_at = EXCLUDED.expires_at,
                        attempts = 0,
                        created_at = now()
                    """,
                    (user_id, otp_hash, expires_at)
                )
                await conn.commit()
    
    async def _send_otp_email(self, email: str, otp: str):
        """Send OTP via email using MailerSend."""
        email_message = (
            EmailBuilder()
            .from_email(settings.MAILERSEND_FROM_EMAIL, "SnapSort")
            .to_many([{"email": email}])
            .subject("Your SnapSort Verification Code")
            .html(f"""
                <h2>Your Verification Code</h2>
                <p>Use the following code to verify your email:</p>
                <h1 style="font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                <p>This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            """)
            .text(f"Your SnapSort verification code is: {otp}. Expires in {settings.OTP_EXPIRY_MINUTES} minutes.")
            .build()
        )
        
        response = self.email_client.emails.send(email_message)
        logger.info("Email sent successfully to: %s", email)
    
    async def verify_otp(self, request: OtpVerificationRequest) -> bool:
        """
        Verify OTP for a user.
        
        Args:
            request: OtpVerificationRequest containing user_id and otp
            
        Returns:
            True if valid, False otherwise
        """
        user_id = str(request.user_id)
        otp_hash = self._hash_otp(request.otp)
        
        try:
            async with asyncio.timeout(5):
                async with self.db_pool.connection() as conn:
                    async with conn.cursor() as cur:
                        # Get stored OTP
                        await cur.execute(
                            """
                            SELECT email_otp_hash, expires_at, attempts 
                            FROM user_otps 
                            WHERE user_id = %s
                            """,
                            (user_id,)
                        )
                        result = await cur.fetchone()
                        
                        if not result:
                            logger.warning("No OTP found for user: %s", user_id)
                            return False
                        
                        # Access as dictionary (psycopg returns dict-like rows)
                        stored_hash = result['email_otp_hash']
                        expires_at = result['expires_at']
                        attempts = result['attempts']
                        
                        # Handle timezone-aware datetime comparison
                        now = datetime.now(timezone.utc)
                        
                        # Convert expires_at to UTC for comparison
                        if expires_at.tzinfo is not None:
                            expires_at_utc = expires_at.astimezone(timezone.utc)
                        else:
                            expires_at_utc = expires_at.replace(tzinfo=timezone.utc)
                        
                        logger.info("Now: %s, Expires: %s", now, expires_at_utc)
                        
                        if now > expires_at_utc:
                            logger.warning("OTP expired for user: %s", user_id)
                            return False
                        
                        # Check attempts
                        if attempts >= settings.MAX_ATTEMPTS:
                            logger.warning("Max OTP attempts exceeded for user: %s", user_id)
                            return False
                        
                        # Increment attempts
                        await cur.execute(
                            "UPDATE user_otps SET attempts = attempts + 1 WHERE user_id = %s",
                            (user_id,)
                        )
                        
                        # Verify hash
                        if otp_hash != stored_hash:
                            await conn.commit()
                            logger.warning("Invalid OTP for user: %s", user_id)
                            return False
                        
                        # Success - delete OTP record
                        await cur.execute(
                            "DELETE FROM user_otps WHERE user_id = %s",
                            (user_id,)
                        )
                        await conn.commit()
                        
                        logger.info("OTP verified successfully for user: %s", user_id)
                        return True
                        
        except asyncio.TimeoutError:
            logger.error("Database timeout verifying OTP for user: %s", user_id)
            raise
        except Exception as e:
            logger.error("Error verifying OTP for user %s: %s", user_id, str(e))
            raise