"""
OTP Service
Handles OTP generation, sending via email, and storage.
"""

import secrets
import hashlib
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

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
        """Generate a secure random OTP."""
        return ''.join(secrets.choice('0123456789') for _ in range(settings.OTP_LENGTH))
    
    def _hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    async def send_and_store_otp(self, user_id: str, email: str) -> bool:
        """
        Generate OTP, send via email, and store hash in database.
        
        Args:
            user_id: User's UUID
            email: User's email address
            
        Returns:
            True if successful, raises exception otherwise
        """
        # Generate OTP
        otp = self._generate_otp()
        otp_hash = self._hash_otp(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        
        logger.info("Sending OTP to: %s", email)
        
        try:
            # Store OTP in database
            async with asyncio.timeout(5):
                await self._store_otp(user_id, otp_hash, expires_at)
            
            # Send email
            await self._send_otp_email(email, otp)
            
            logger.info("OTP sent successfully to: %s", email)
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout sending/storing OTP for: %s", email)
            raise
        except Exception as e:
            logger.error("Error sending OTP to %s: %s", email, str(e))
            raise
    
    async def _store_otp(self, user_id: str, otp_hash: str, expires_at: datetime):
        """Store OTP hash in database."""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cur:
                # Upsert - update if exists, insert if not
                await cur.execute(
                    """
                    INSERT INTO user_otps (id, user_id, email_otp_hash, expires_at, attempts)
                    VALUES (%s, %s, %s, %s, 0)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_otp_hash = EXCLUDED.email_otp_hash,
                        expires_at = EXCLUDED.expires_at,
                        attempts = 0,
                        created_at = now()
                    """,
                    (str(uuid4()), user_id, otp_hash, expires_at)
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
        logger.info("Email sent, message_id: %s", response.message_id)
    
    async def verify_otp(self, user_id: str, otp: str) -> bool:
        """
        Verify OTP for a user.
        
        Args:
            user_id: User's UUID
            otp: OTP to verify
            
        Returns:
            True if valid, False otherwise
        """
        otp_hash = self._hash_otp(otp)
        
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
                        
                        stored_hash, expires_at, attempts = result
                        
                        # Check expiry
                        if datetime.utcnow() > expires_at:
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